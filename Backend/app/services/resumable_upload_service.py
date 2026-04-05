from __future__ import annotations

import hashlib
import json
import string
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from fastapi import HTTPException, status

from app.core.config import settings
from app.services.upload_service import ALLOWED_VIDEO_EXTENSIONS, ensure_upload_dir


DEFAULT_CHUNK_SIZE_BYTES = 2 * 1024 * 1024
MIN_CHUNK_SIZE_BYTES = 256 * 1024
MAX_CHUNK_SIZE_BYTES = 8 * 1024 * 1024
SESSION_TTL_SECONDS = 7 * 24 * 60 * 60

UPLOAD_STATUS_IN_PROGRESS = "in-progress"
UPLOAD_STATUS_COMPLETED = "completed"


def _now_utc() -> datetime:
    return datetime.now(UTC)


def _isoformat(value: datetime) -> str:
    return value.isoformat()


def _parse_iso_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _safe_int(value: Any, fallback: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def _resumable_dirs() -> tuple[Path, Path]:
    root = ensure_upload_dir() / ".resumable"
    sessions_dir = root / "sessions"
    parts_dir = root / "parts"
    sessions_dir.mkdir(parents=True, exist_ok=True)
    parts_dir.mkdir(parents=True, exist_ok=True)
    return sessions_dir, parts_dir


def _sanitize_filename(file_name: str) -> str:
    return Path(file_name).name.replace(" ", "_").strip()


def _validate_video_filename(file_name: str) -> str:
    sanitized_name = _sanitize_filename(file_name)
    if not sanitized_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must include a filename.",
        )

    suffix = Path(sanitized_name).suffix.lower()
    if suffix not in ALLOWED_VIDEO_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only video uploads are allowed (.mp4, .mov, .mkv, .webm, .avi).",
        )
    return sanitized_name


def _normalize_upload_id(upload_id: str) -> str:
    normalized = str(upload_id or "").strip().lower()
    allowed = set(string.hexdigits.lower())
    if len(normalized) != 64 or any(char not in allowed for char in normalized):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Upload id is invalid.",
        )
    return normalized


def _session_path(upload_id: str) -> Path:
    sessions_dir, _ = _resumable_dirs()
    return sessions_dir / f"{upload_id}.json"


def _part_path(upload_id: str) -> Path:
    _, parts_dir = _resumable_dirs()
    return parts_dir / f"{upload_id}.part"


def _load_session(upload_id: str) -> dict[str, Any] | None:
    path = _session_path(upload_id)
    if not path.exists():
        return None

    try:
        content = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        path.unlink(missing_ok=True)
        return None

    if not isinstance(content, dict):
        path.unlink(missing_ok=True)
        return None

    return content


def _save_session(upload_id: str, session_payload: dict[str, Any]) -> None:
    path = _session_path(upload_id)
    temp_path = path.with_suffix(".tmp")
    serialized = json.dumps(session_payload, ensure_ascii=True, separators=(",", ":"))
    temp_path.write_text(serialized, encoding="utf-8")
    temp_path.replace(path)


def _delete_session(upload_id: str, remove_part: bool = True) -> None:
    _session_path(upload_id).unlink(missing_ok=True)
    if remove_part:
        _part_path(upload_id).unlink(missing_ok=True)


def _is_expired(session_payload: dict[str, Any], now: datetime) -> bool:
    expires_at = _parse_iso_datetime(session_payload.get("expires_at"))
    if expires_at is None:
        return True
    return expires_at <= now


def _resolve_chunk_size(preferred_chunk_size_bytes: int | None) -> int:
    if preferred_chunk_size_bytes is None:
        return DEFAULT_CHUNK_SIZE_BYTES

    preferred = _safe_int(preferred_chunk_size_bytes, DEFAULT_CHUNK_SIZE_BYTES)
    if preferred < MIN_CHUNK_SIZE_BYTES:
        return MIN_CHUNK_SIZE_BYTES
    if preferred > MAX_CHUNK_SIZE_BYTES:
        return MAX_CHUNK_SIZE_BYTES
    return preferred


def _build_upload_id(user_id: int, use_case_id: int, upload_kind: str, upload_key: str) -> str:
    key_material = f"{user_id}:{use_case_id}:{upload_kind}:{upload_key.strip()}"
    return hashlib.sha256(key_material.encode("utf-8")).hexdigest()


def _refresh_received_bytes(upload_id: str, session_payload: dict[str, Any]) -> None:
    if session_payload.get("status") == UPLOAD_STATUS_COMPLETED:
        session_payload["received_bytes"] = _safe_int(session_payload.get("file_size_bytes"), 0)
        return

    part_file = _part_path(upload_id)
    if part_file.exists():
        session_payload["received_bytes"] = _safe_int(part_file.stat().st_size, 0)
    else:
        session_payload["received_bytes"] = 0


def start_or_resume_upload_session(
    *,
    user_id: int,
    use_case_id: int,
    upload_kind: str,
    upload_key: str,
    file_name: str,
    file_size_bytes: int,
    content_type: str | None,
    preferred_chunk_size_bytes: int | None,
) -> dict[str, Any]:
    normalized_kind = str(upload_kind or "").strip().lower()
    if normalized_kind not in {"meeting", "demo"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Upload kind must be either 'meeting' or 'demo'.",
        )

    normalized_upload_key = str(upload_key or "").strip()
    if len(normalized_upload_key) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Upload key is required for resumable uploads.",
        )

    sanitized_name = _validate_video_filename(file_name)
    declared_size = _safe_int(file_size_bytes, 0)
    if declared_size <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size must be greater than zero.",
        )

    max_size_bytes = settings.max_upload_size_mb * 1024 * 1024
    if declared_size > max_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Video file exceeds {settings.max_upload_size_mb} MB limit.",
        )

    chunk_size = _resolve_chunk_size(preferred_chunk_size_bytes)
    now = _now_utc()
    expires_at = now + timedelta(seconds=SESSION_TTL_SECONDS)
    upload_id = _build_upload_id(user_id, use_case_id, normalized_kind, normalized_upload_key)

    session = _load_session(upload_id)
    if session is not None:
        if _safe_int(session.get("user_id"), -1) != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Upload session not found.",
            )

        if _is_expired(session, now) and session.get("status") != UPLOAD_STATUS_COMPLETED:
            _delete_session(upload_id, remove_part=True)
            session = None
        else:
            existing_kind = str(session.get("upload_kind") or "").strip().lower()
            existing_use_case_id = _safe_int(session.get("use_case_id"), -1)
            existing_size = _safe_int(session.get("file_size_bytes"), 0)
            existing_name = str(session.get("file_name") or "")
            if (
                existing_kind != normalized_kind
                or existing_use_case_id != use_case_id
                or existing_size != declared_size
                or existing_name != sanitized_name
            ):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Upload key already belongs to a different file. Choose the original file to resume.",
                )

            _refresh_received_bytes(upload_id, session)
            session["chunk_size_bytes"] = chunk_size
            session["updated_at"] = _isoformat(now)
            session["expires_at"] = _isoformat(expires_at)
            _save_session(upload_id, session)
            return session

    part_file = _part_path(upload_id)
    part_file.parent.mkdir(parents=True, exist_ok=True)
    part_file.touch(exist_ok=True)

    session = {
        "upload_id": upload_id,
        "user_id": user_id,
        "use_case_id": use_case_id,
        "upload_kind": normalized_kind,
        "file_name": sanitized_name,
        "file_size_bytes": declared_size,
        "content_type": content_type,
        "chunk_size_bytes": chunk_size,
        "received_bytes": 0,
        "status": UPLOAD_STATUS_IN_PROGRESS,
        "stored_path": None,
        "created_at": _isoformat(now),
        "updated_at": _isoformat(now),
        "expires_at": _isoformat(expires_at),
    }
    _save_session(upload_id, session)
    return session


def get_upload_session(upload_id: str, user_id: int) -> dict[str, Any]:
    normalized_upload_id = _normalize_upload_id(upload_id)
    session = _load_session(normalized_upload_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Upload session not found.",
        )

    if _safe_int(session.get("user_id"), -1) != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Upload session not found.",
        )

    now = _now_utc()
    if _is_expired(session, now) and session.get("status") != UPLOAD_STATUS_COMPLETED:
        _delete_session(normalized_upload_id, remove_part=True)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Upload session expired. Please restart the upload.",
        )

    _refresh_received_bytes(normalized_upload_id, session)
    session["updated_at"] = _isoformat(now)
    session["expires_at"] = _isoformat(now + timedelta(seconds=SESSION_TTL_SECONDS))
    _save_session(normalized_upload_id, session)
    return session


def append_upload_chunk(
    *,
    upload_id: str,
    user_id: int,
    expected_offset: int,
    chunk_payload: bytes,
) -> dict[str, Any]:
    normalized_upload_id = _normalize_upload_id(upload_id)
    if expected_offset < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Upload offset must be non-negative.",
        )

    if not chunk_payload:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Chunk payload is empty.",
        )

    session = get_upload_session(normalized_upload_id, user_id)
    if session.get("status") == UPLOAD_STATUS_COMPLETED:
        file_size = _safe_int(session.get("file_size_bytes"), 0)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "UPLOAD_ALREADY_COMPLETED",
                "message": "Upload is already completed.",
                "received_bytes": file_size,
                "file_size_bytes": file_size,
            },
        )

    current_received = _safe_int(session.get("received_bytes"), 0)
    if expected_offset != current_received:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "UPLOAD_OFFSET_MISMATCH",
                "message": "Upload offset does not match server state.",
                "received_bytes": current_received,
                "file_size_bytes": _safe_int(session.get("file_size_bytes"), 0),
            },
        )

    file_size = _safe_int(session.get("file_size_bytes"), 0)
    next_received = current_received + len(chunk_payload)
    if next_received > file_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Chunk exceeds declared file size.",
        )

    part_file = _part_path(normalized_upload_id)
    part_file.parent.mkdir(parents=True, exist_ok=True)
    with part_file.open("ab") as output:
        output.write(chunk_payload)

    now = _now_utc()
    session["received_bytes"] = next_received
    session["updated_at"] = _isoformat(now)
    session["expires_at"] = _isoformat(now + timedelta(seconds=SESSION_TTL_SECONDS))
    _save_session(normalized_upload_id, session)
    return session


def finalize_upload_session(
    *,
    upload_id: str,
    user_id: int,
    stored_name_prefix: str,
) -> dict[str, Any]:
    normalized_upload_id = _normalize_upload_id(upload_id)
    session = get_upload_session(normalized_upload_id, user_id)

    file_size = _safe_int(session.get("file_size_bytes"), 0)
    if session.get("status") == UPLOAD_STATUS_COMPLETED:
        session["received_bytes"] = file_size
        return session

    current_received = _safe_int(session.get("received_bytes"), 0)
    if current_received != file_size:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "UPLOAD_NOT_COMPLETE",
                "message": "Upload is not complete yet.",
                "received_bytes": current_received,
                "file_size_bytes": file_size,
            },
        )

    file_name = str(session.get("file_name") or "")
    suffix = Path(file_name).suffix.lower()
    if suffix not in ALLOWED_VIDEO_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only video uploads are allowed (.mp4, .mov, .mkv, .webm, .avi).",
        )

    stored_name = str(session.get("stored_name") or "").strip()
    if not stored_name:
        stored_name = f"{stored_name_prefix}{normalized_upload_id[:24]}{suffix}"

    destination = ensure_upload_dir() / stored_name
    part_file = _part_path(normalized_upload_id)
    if not part_file.exists():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Upload data is missing on server. Please restart the upload.",
        )

    if not destination.exists():
        part_file.replace(destination)
    else:
        existing_size = _safe_int(destination.stat().st_size, -1)
        if existing_size != file_size:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Stored upload has inconsistent size. Please restart with a new upload key.",
            )
        part_file.unlink(missing_ok=True)

    now = _now_utc()
    session["status"] = UPLOAD_STATUS_COMPLETED
    session["received_bytes"] = file_size
    session["stored_name"] = stored_name
    session["stored_path"] = str(destination)
    session["updated_at"] = _isoformat(now)
    session["expires_at"] = _isoformat(now + timedelta(seconds=SESSION_TTL_SECONDS))
    _save_session(normalized_upload_id, session)
    return session


def cancel_upload_session(upload_id: str, user_id: int) -> None:
    normalized_upload_id = _normalize_upload_id(upload_id)
    session = get_upload_session(normalized_upload_id, user_id)
    remove_part = session.get("status") != UPLOAD_STATUS_COMPLETED
    _delete_session(normalized_upload_id, remove_part=remove_part)

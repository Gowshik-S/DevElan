from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status

from app.core.config import settings


ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".webm", ".avi"}


def ensure_upload_dir() -> Path:
    upload_path = Path(settings.upload_dir)
    upload_path.mkdir(parents=True, exist_ok=True)
    return upload_path


def _sanitize_filename(file_name: str) -> str:
    return Path(file_name).name.replace(" ", "_")


def save_uploaded_video(file: UploadFile) -> tuple[str, str, int]:
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must include a filename.",
        )

    sanitized_name = _sanitize_filename(file.filename)
    suffix = Path(sanitized_name).suffix.lower()
    if suffix not in ALLOWED_VIDEO_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only video uploads are allowed (.mp4, .mov, .mkv, .webm, .avi).",
        )

    upload_dir = ensure_upload_dir()
    stored_name = f"{uuid4().hex}{suffix}"
    destination = upload_dir / stored_name
    max_size_bytes = settings.max_upload_size_mb * 1024 * 1024

    size_bytes = 0
    try:
        with destination.open("wb") as output:
            while True:
                chunk = file.file.read(1024 * 1024)
                if not chunk:
                    break
                size_bytes += len(chunk)
                if size_bytes > max_size_bytes:
                    output.close()
                    destination.unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"Video file exceeds {settings.max_upload_size_mb} MB limit.",
                    )
                output.write(chunk)
    finally:
        file.file.close()

    return str(destination), sanitized_name, size_bytes

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.dependencies import bearer_scheme, get_current_user
from app.core.security import create_video_stream_token, decode_access_token, decode_video_stream_token
from app.db.session import get_db
from app.models.submission import VideoAsset
from app.models.user import User, UserRole

router = APIRouter(prefix="/video", tags=["Video"])


def _resolve_user_from_bearer(
    credentials: HTTPAuthorizationCredentials | None,
    db: Session,
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials.",
        )

    try:
        payload = decode_access_token(credentials.credentials)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc

    raw_subject = payload.get("sub")
    if raw_subject is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload is missing subject.",
        )

    try:
        user_id = int(raw_subject)
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token subject is invalid.",
        ) from exc

    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User is not available.",
        )
    return user


def _resolve_user_from_stream_token(stream_token: str, video_id: int, db: Session) -> User:
    try:
        payload = decode_video_stream_token(stream_token)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc

    try:
        token_video_id = int(payload.get("video_id"))
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Stream token has invalid video id.",
        ) from exc

    if token_video_id != video_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Stream token does not match requested video.",
        )

    try:
        user_id = int(payload.get("sub"))
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Stream token has invalid subject.",
        ) from exc

    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User is not available.",
        )
    return user


def _resolve_stream_user(
    *,
    db: Session,
    credentials: HTTPAuthorizationCredentials | None,
    stream_token: str | None,
    video_id: int,
) -> User:
    if stream_token:
        return _resolve_user_from_stream_token(stream_token, video_id, db)
    return _resolve_user_from_bearer(credentials, db)


def _load_video_asset(video_id: int, db: Session) -> VideoAsset:
    asset = db.get(VideoAsset, video_id)
    if asset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video asset not found.",
        )
    return asset


def _ensure_video_access(current_user: User, asset: VideoAsset) -> None:
    if current_user.role != UserRole.ADMIN and asset.submission.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this video.",
        )


@router.get("/stream-token/{video_id}")
def get_stream_token(
    video_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, int | str]:
    asset = _load_video_asset(video_id, db)
    _ensure_video_access(current_user, asset)

    stream_token = create_video_stream_token(current_user.id, video_id)
    return {
        "stream_token": stream_token,
        "expires_in_seconds": 600,
    }


@router.get("/stream/{video_id}")
def stream_video(
    video_id: int,
    st: str | None = Query(default=None),
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> FileResponse:
    current_user = _resolve_stream_user(
        db=db,
        credentials=credentials,
        stream_token=st,
        video_id=video_id,
    )
    asset = _load_video_asset(video_id, db)
    _ensure_video_access(current_user, asset)

    target = Path(asset.stored_path)
    if not target.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video file is missing on disk.",
        )

    media_type = asset.content_type or "video/mp4"
    response = FileResponse(target, media_type=media_type, filename=asset.original_file_name)
    response.headers.setdefault("Accept-Ranges", "bytes")
    return response

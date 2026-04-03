from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.submission import VideoAsset
from app.models.user import User, UserRole

router = APIRouter(prefix="/video", tags=["Video"])


@router.get("/stream/{video_id}")
def stream_video(
    video_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FileResponse:
    asset = db.get(VideoAsset, video_id)
    if asset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video asset not found.",
        )

    if current_user.role != UserRole.ADMIN and asset.submission.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this video.",
        )

    target = Path(asset.stored_path)
    if not target.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video file is missing on disk.",
        )

    media_type = asset.content_type or "video/mp4"
    return FileResponse(target, media_type=media_type, filename=asset.original_file_name)

from pathlib import Path

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.dependencies import require_admin
from app.db.session import get_db
from app.models.submission import Submission, VideoAsset
from app.models.usecase import UseCase
from app.models.user import User
from app.schemas.submission import (
    StatusUpdateRequest,
    StatusUpdateResponse,
    SubmissionListItem,
    SubmissionListResponse,
)

router = APIRouter(prefix="/submissions", tags=["Submissions"])


DEMO_VIDEO_PREFIX = "demo_"


def _is_demo_video_asset(asset: VideoAsset) -> bool:
    return Path(asset.stored_path).name.lower().startswith(DEMO_VIDEO_PREFIX)


def _get_submission_video_assets(db: Session, submission_id: int) -> tuple[VideoAsset | None, VideoAsset | None]:
    assets = db.scalars(
        select(VideoAsset)
        .where(VideoAsset.submission_id == submission_id)
        .order_by(VideoAsset.created_at.desc())
    ).all()

    meeting_asset: VideoAsset | None = None
    demo_asset: VideoAsset | None = None
    for asset in assets:
        if _is_demo_video_asset(asset):
            if demo_asset is None:
                demo_asset = asset
        elif meeting_asset is None:
            meeting_asset = asset

        if meeting_asset and demo_asset:
            break

    return meeting_asset, demo_asset


def _build_submission_item(db: Session, submission: Submission) -> SubmissionListItem:
    meeting_asset, demo_asset = _get_submission_video_assets(db, submission.id)

    return SubmissionListItem(
        submission_id=submission.id,
        user_name=submission.user.full_name,
        register_no=submission.user.register_no,
        project_title=submission.usecase.title,
        repo_link=submission.repo_url,
        video_id=meeting_asset.id if meeting_asset else None,
        meeting_video_id=meeting_asset.id if meeting_asset else None,
        demo_video_id=demo_asset.id if demo_asset else None,
        status=submission.status,
    )


@router.get("/list", response_model=SubmissionListResponse)
def list_submissions(
    filter_query: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> SubmissionListResponse:
    query = select(Submission).join(Submission.user).join(Submission.usecase)

    if filter_query:
        search_pattern = f"%{filter_query.strip()}%"
        query = query.where(
            or_(
                User.full_name.ilike(search_pattern),
                User.register_no.ilike(search_pattern),
                UseCase.title.ilike(search_pattern),
                Submission.repo_url.ilike(search_pattern),
            )
        )

    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = db.scalars(
        query
        .order_by(Submission.updated_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    ).all()

    items = [_build_submission_item(db, row) for row in rows]
    return SubmissionListResponse(page=page, limit=limit, total=total, submissions=items)


@router.get("/get/{submission_id}", response_model=SubmissionListItem)
def get_submission_detail(
    submission_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> SubmissionListItem:
    submission = db.get(Submission, submission_id)
    if submission is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found.",
        )
    return _build_submission_item(db, submission)


@router.patch("/update-status", response_model=StatusUpdateResponse)
def update_submission_status(
    payload: StatusUpdateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> StatusUpdateResponse:
    submission = db.get(Submission, payload.submission_id)
    if submission is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found.",
        )

    submission.status = payload.status
    db.add(submission)
    db.commit()

    return StatusUpdateResponse(
        success=True,
        submission_id=submission.id,
        updated_status=submission.status,
    )

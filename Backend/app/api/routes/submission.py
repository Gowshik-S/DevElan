from sqlalchemy import func, select
from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.submission import Submission, SubmissionStatus, VideoAsset
from app.models.usecase import UseCase, UseCaseAssignment
from app.models.user import User, UserRole
from app.schemas.submission import (
    RepoLinkSubmissionRequest,
    RepoLinkSubmissionResponse,
    SubmissionDetail,
    VideoUploadResponse,
)
from app.services.upload_service import save_uploaded_video

router = APIRouter(prefix="/submission", tags=["Submission"])


def _find_use_case(db: Session, use_case_id: str) -> UseCase | None:
    normalized = use_case_id.strip()
    if normalized.isdigit():
        return db.get(UseCase, int(normalized))
    return db.scalar(select(UseCase).where(UseCase.code.ilike(normalized)))


def _derive_status(repo_url: str | None, has_video: bool) -> SubmissionStatus:
    if repo_url and has_video:
        return SubmissionStatus.SUBMITTED
    if repo_url and not has_video:
        return SubmissionStatus.IN_PROGRESS
    if not repo_url and has_video:
        return SubmissionStatus.WAITING
    return SubmissionStatus.PENDING


def _ensure_use_case_access(db: Session, user: User, use_case: UseCase) -> None:
    if user.role == UserRole.ADMIN:
        return

    assignment = db.scalar(
        select(UseCaseAssignment).where(
            UseCaseAssignment.user_id == user.id,
            UseCaseAssignment.usecase_id == use_case.id,
        )
    )
    if assignment is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Use case is not assigned to this user.",
        )


def _get_or_create_submission(db: Session, user_id: int, use_case_id: int) -> Submission:
    submission = db.scalar(
        select(Submission).where(
            Submission.user_id == user_id,
            Submission.usecase_id == use_case_id,
        )
    )
    if submission is None:
        submission = Submission(user_id=user_id, usecase_id=use_case_id)
        db.add(submission)
        db.flush()
    return submission


@router.post("/repo-link", response_model=RepoLinkSubmissionResponse)
def submit_repo_link(
    payload: RepoLinkSubmissionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RepoLinkSubmissionResponse:
    use_case = _find_use_case(db, payload.use_case_id)
    if use_case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Use case not found.",
        )

    _ensure_use_case_access(db, current_user, use_case)
    submission = _get_or_create_submission(db, current_user.id, use_case.id)
    submission.repo_url = str(payload.repo_url)

    has_video = (db.scalar(
        select(func.count(VideoAsset.id)).where(VideoAsset.submission_id == submission.id)
    ) or 0) > 0
    submission.status = _derive_status(submission.repo_url, has_video)

    db.add(submission)
    db.commit()
    db.refresh(submission)

    return RepoLinkSubmissionResponse(
        success=True,
        repo_id=submission.id,
        status=submission.status,
        message="Repository link submitted successfully.",
    )


@router.post("/video-upload", response_model=VideoUploadResponse)
def upload_video(
    use_case_id: str = Form(...),
    video_file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> VideoUploadResponse:
    use_case = _find_use_case(db, use_case_id)
    if use_case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Use case not found.",
        )

    _ensure_use_case_access(db, current_user, use_case)
    submission = _get_or_create_submission(db, current_user.id, use_case.id)

    stored_path, original_name, size_bytes = save_uploaded_video(video_file)
    asset = VideoAsset(
        submission_id=submission.id,
        original_file_name=original_name,
        stored_path=stored_path,
        content_type=video_file.content_type,
        size_bytes=size_bytes,
    )
    db.add(asset)

    submission.status = _derive_status(submission.repo_url, True)
    db.add(submission)
    db.commit()
    db.refresh(asset)

    return VideoUploadResponse(
        success=True,
        video_id=asset.id,
        status=submission.status,
        message="Video uploaded successfully.",
    )


@router.get("/get", response_model=list[SubmissionDetail])
def get_submissions(
    use_case_id: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[SubmissionDetail]:
    query = select(Submission).where(Submission.user_id == current_user.id)
    if use_case_id:
        use_case = _find_use_case(db, use_case_id)
        if use_case is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Use case not found.",
            )
        query = query.where(Submission.usecase_id == use_case.id)

    submissions = db.scalars(query.order_by(Submission.updated_at.desc())).all()
    response: list[SubmissionDetail] = []
    for submission in submissions:
        latest_asset = db.scalar(
            select(VideoAsset)
            .where(VideoAsset.submission_id == submission.id)
            .order_by(VideoAsset.created_at.desc())
        )

        response.append(
            SubmissionDetail(
                submission_id=submission.id,
                use_case_id=submission.usecase_id,
                use_case_code=submission.usecase.code,
                project_title=submission.usecase.title,
                repo_url=submission.repo_url,
                video_id=latest_asset.id if latest_asset else None,
                status=submission.status,
            )
        )

    return response

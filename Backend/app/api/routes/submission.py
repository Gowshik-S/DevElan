from pathlib import Path
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, Request, UploadFile, status

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.submission import Submission, SubmissionStatus, VideoAsset
from app.models.usecase import UseCase, UseCaseAssignment
from app.models.user import User, UserRole
from app.schemas.submission import (
    ResumableUploadCancelResponse,
    ResumableUploadChunkResponse,
    ResumableUploadSessionResponse,
    ResumableUploadStartRequest,
    RepoLinkSubmissionRequest,
    RepoLinkSubmissionResponse,
    SubmissionDetail,
    VideoUploadResponse,
)
from app.services.resumable_upload_service import (
    append_upload_chunk,
    cancel_upload_session,
    finalize_upload_session,
    get_upload_session,
    start_or_resume_upload_session,
)
from app.services.upload_service import save_uploaded_video

router = APIRouter(prefix="/submission", tags=["Submission"])


MEETING_VIDEO_PREFIX = "meeting_"
DEMO_VIDEO_PREFIX = "demo_"


def _parse_session_datetime(raw_value: object) -> datetime:
    if isinstance(raw_value, str):
        try:
            parsed = datetime.fromisoformat(raw_value)
            if parsed.tzinfo is None:
                return parsed.replace(tzinfo=UTC)
            return parsed.astimezone(UTC)
        except ValueError:
            pass
    return datetime.now(UTC)


def _build_resumable_session_response(
    session_payload: dict[str, object],
    *,
    message: str,
) -> ResumableUploadSessionResponse:
    file_size_bytes = int(session_payload.get("file_size_bytes") or 0)
    received_bytes = int(session_payload.get("received_bytes") or 0)
    upload_kind = str(session_payload.get("upload_kind") or "meeting").lower()

    return ResumableUploadSessionResponse(
        upload_id=str(session_payload.get("upload_id") or ""),
        upload_kind="demo" if upload_kind == "demo" else "meeting",
        file_name=str(session_payload.get("file_name") or ""),
        file_size_bytes=file_size_bytes,
        chunk_size_bytes=int(session_payload.get("chunk_size_bytes") or 0),
        received_bytes=received_bytes,
        complete=received_bytes >= file_size_bytes,
        expires_at=_parse_session_datetime(session_payload.get("expires_at")),
        message=message,
    )


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


@router.post("/resumable/start", response_model=ResumableUploadSessionResponse)
def start_resumable_video_upload(
    payload: ResumableUploadStartRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ResumableUploadSessionResponse:
    use_case = _find_use_case(db, payload.use_case_id)
    if use_case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Use case not found.",
        )

    _ensure_use_case_access(db, current_user, use_case)
    session_payload = start_or_resume_upload_session(
        user_id=current_user.id,
        use_case_id=use_case.id,
        upload_kind=payload.upload_kind,
        upload_key=payload.upload_key,
        file_name=payload.file_name,
        file_size_bytes=payload.file_size_bytes,
        content_type=payload.content_type,
        preferred_chunk_size_bytes=payload.preferred_chunk_size_bytes,
    )

    resumed_bytes = int(session_payload.get("received_bytes") or 0)
    complete = resumed_bytes >= int(session_payload.get("file_size_bytes") or 0)
    if complete:
        message = "Upload already completed on server."
    elif resumed_bytes > 0:
        message = "Resuming upload from last confirmed byte."
    else:
        message = "Resumable upload session created."

    return _build_resumable_session_response(session_payload, message=message)


@router.get("/resumable/{upload_id}/status", response_model=ResumableUploadSessionResponse)
def get_resumable_video_upload_status(
    upload_id: str,
    current_user: User = Depends(get_current_user),
) -> ResumableUploadSessionResponse:
    session_payload = get_upload_session(upload_id, current_user.id)
    return _build_resumable_session_response(
        session_payload,
        message="Resumable upload status fetched.",
    )


@router.put("/resumable/{upload_id}/chunk", response_model=ResumableUploadChunkResponse)
async def upload_resumable_video_chunk(
    upload_id: str,
    request: Request,
    upload_offset: int = Header(..., alias="X-Upload-Offset"),
    current_user: User = Depends(get_current_user),
) -> ResumableUploadChunkResponse:
    chunk_payload = await request.body()
    session_payload = append_upload_chunk(
        upload_id=upload_id,
        user_id=current_user.id,
        expected_offset=upload_offset,
        chunk_payload=chunk_payload,
    )

    file_size_bytes = int(session_payload.get("file_size_bytes") or 0)
    received_bytes = int(session_payload.get("received_bytes") or 0)
    return ResumableUploadChunkResponse(
        upload_id=str(session_payload.get("upload_id") or upload_id),
        received_bytes=received_bytes,
        file_size_bytes=file_size_bytes,
        complete=received_bytes >= file_size_bytes,
    )


@router.post("/resumable/{upload_id}/complete", response_model=VideoUploadResponse)
def complete_resumable_video_upload(
    upload_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> VideoUploadResponse:
    session_payload = get_upload_session(upload_id, current_user.id)
    upload_kind = str(session_payload.get("upload_kind") or "meeting").lower()
    use_case_id = int(session_payload.get("use_case_id") or 0)

    use_case = db.get(UseCase, use_case_id)
    if use_case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Use case not found.",
        )

    _ensure_use_case_access(db, current_user, use_case)
    stored_name_prefix = DEMO_VIDEO_PREFIX if upload_kind == "demo" else MEETING_VIDEO_PREFIX
    finalized_session = finalize_upload_session(
        upload_id=upload_id,
        user_id=current_user.id,
        stored_name_prefix=stored_name_prefix,
    )

    stored_path = str(finalized_session.get("stored_path") or "").strip()
    if not stored_path:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Upload finalized but stored path is missing.",
        )

    submission = _get_or_create_submission(db, current_user.id, use_case.id)
    existing_asset = db.scalar(select(VideoAsset).where(VideoAsset.stored_path == stored_path))

    if existing_asset is None:
        existing_asset = VideoAsset(
            submission_id=submission.id,
            original_file_name=str(finalized_session.get("file_name") or "video"),
            stored_path=stored_path,
            content_type=finalized_session.get("content_type") if isinstance(finalized_session.get("content_type"), str) else None,
            size_bytes=int(finalized_session.get("file_size_bytes") or 0),
        )
        db.add(existing_asset)

    if upload_kind == "meeting":
        submission.status = _derive_status(submission.repo_url, True)
    else:
        meeting_asset, _ = _get_submission_video_assets(db, submission.id)
        submission.status = _derive_status(submission.repo_url, meeting_asset is not None)

    db.add(submission)
    db.commit()
    db.refresh(existing_asset)

    return VideoUploadResponse(
        success=True,
        video_id=existing_asset.id,
        video_type="demo" if upload_kind == "demo" else "meeting",
        status=submission.status,
        message=(
            "Demo video uploaded successfully."
            if upload_kind == "demo"
            else "Meeting video uploaded successfully."
        ),
    )


@router.delete("/resumable/{upload_id}", response_model=ResumableUploadCancelResponse)
def cancel_resumable_video_upload(
    upload_id: str,
    current_user: User = Depends(get_current_user),
) -> ResumableUploadCancelResponse:
    cancel_upload_session(upload_id, current_user.id)
    return ResumableUploadCancelResponse(
        success=True,
        message="Resumable upload session cancelled.",
    )


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

    meeting_asset, _ = _get_submission_video_assets(db, submission.id)
    submission.status = _derive_status(submission.repo_url, meeting_asset is not None)

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

    stored_path, original_name, size_bytes = save_uploaded_video(
        video_file,
        stored_name_prefix=MEETING_VIDEO_PREFIX,
    )
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
        video_type="meeting",
        status=submission.status,
        message="Meeting video uploaded successfully.",
    )


@router.post("/demo-video-upload", response_model=VideoUploadResponse)
def upload_demo_video(
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
    meeting_asset, _ = _get_submission_video_assets(db, submission.id)

    stored_path, original_name, size_bytes = save_uploaded_video(
        video_file,
        stored_name_prefix=DEMO_VIDEO_PREFIX,
    )
    asset = VideoAsset(
        submission_id=submission.id,
        original_file_name=original_name,
        stored_path=stored_path,
        content_type=video_file.content_type,
        size_bytes=size_bytes,
    )
    db.add(asset)

    submission.status = _derive_status(submission.repo_url, meeting_asset is not None)
    db.add(submission)
    db.commit()
    db.refresh(asset)

    return VideoUploadResponse(
        success=True,
        video_id=asset.id,
        video_type="demo",
        status=submission.status,
        message="Demo video uploaded successfully.",
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
        meeting_asset, demo_asset = _get_submission_video_assets(db, submission.id)

        response.append(
            SubmissionDetail(
                submission_id=submission.id,
                use_case_id=submission.usecase_id,
                use_case_code=submission.usecase.code,
                project_title=submission.usecase.title,
                repo_url=submission.repo_url,
                video_id=meeting_asset.id if meeting_asset else None,
                meeting_video_id=meeting_asset.id if meeting_asset else None,
                demo_video_id=demo_asset.id if demo_asset else None,
                status=submission.status,
            )
        )

    return response

from pathlib import Path
from datetime import UTC, datetime
import logging

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.dependencies import require_admin
from app.db.session import get_db
from app.models.submission import (
    Submission,
    SubmissionEvaluation,
    SubmissionEvaluationDecision,
    SubmissionMailNotification,
    SubmissionMailType,
    VideoAsset,
)
from app.models.usecase import UseCase
from app.models.user import User
from app.schemas.submission import (
    SubmissionEvaluationMailRequest,
    SubmissionEvaluationMailResponse,
    SubmissionEvaluationUpdateRequest,
    SubmissionEvaluationUpdateResponse,
    StatusUpdateRequest,
    StatusUpdateResponse,
    SubmissionListItem,
    SubmissionListResponse,
)
from app.services.mail import send_submission_mail

router = APIRouter(prefix="/submissions", tags=["Submissions"])
logger = logging.getLogger(__name__)


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
    evaluation = submission.evaluation
    mail_notification = submission.mail_notification

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
        evaluation_decision=evaluation.decision if evaluation else None,
        admin_feedback=evaluation.feedback if evaluation else None,
        mail_sent_count=mail_notification.sent_count if mail_notification else 0,
        last_mail_type=mail_notification.last_mail_type if mail_notification else None,
        last_mail_sent_at=mail_notification.last_sent_at if mail_notification else None,
    )


def _build_acceptance_mail_content(
    submission: Submission,
    evaluation: SubmissionEvaluation | None,
) -> tuple[str, str, SubmissionMailType]:
    student_name = submission.user.full_name or "Student"
    project_title = submission.usecase.title or "your project"
    decision = evaluation.decision if evaluation else SubmissionEvaluationDecision.PENDING

    if decision == SubmissionEvaluationDecision.ACCEPTED:
        subject = "Project Acceptance Notification - DevElan"
        body = (
            f"Dear {student_name},\n\n"
            f"We are pleased to inform you that your project submission titled '{project_title}' has been formally accepted by the evaluation panel.\n"
            "Your submission has been successfully received and reviewed.\n\n"
            "Congratulations, and thank you for your effort.\n\n"
            "Sincerely,\n"
            "DevElan Evaluation Team"
        )
    elif decision == SubmissionEvaluationDecision.REJECTED:
        subject = "Project Evaluation Result - DevElan"
        body = (
            f"Dear {student_name},\n\n"
            f"Thank you for submitting your project titled '{project_title}'.\n"
            "After review, your current evaluation status is Rejected.\n"
            "Please do not be discouraged. Detailed feedback and improvement guidance will be shared by the admin.\n\n"
            "You may revise and resubmit based on the provided feedback.\n\n"
            "Sincerely,\n"
            "DevElan Evaluation Team"
        )
    else:
        subject = "Project Submission Received - DevElan"
        body = (
            f"Dear {student_name},\n\n"
            f"We acknowledge receipt of your project submission titled '{project_title}'.\n"
            "Your submission is currently under review, and a formal evaluation update will be communicated shortly.\n\n"
            "Sincerely,\n"
            "DevElan Evaluation Team"
        )

    return subject, body, SubmissionMailType.ACCEPTANCE


def _build_feedback_mail_content(
    submission: Submission,
    evaluation: SubmissionEvaluation | None,
) -> tuple[str, str, SubmissionMailType]:
    student_name = submission.user.full_name or "Student"
    project_title = submission.usecase.title or "your project"
    decision = evaluation.decision if evaluation else SubmissionEvaluationDecision.PENDING
    feedback = (evaluation.feedback or "").strip() if evaluation else ""

    if feedback:
        decision_label = {
            SubmissionEvaluationDecision.ACCEPTED: "Accepted",
            SubmissionEvaluationDecision.REJECTED: "Rejected",
            SubmissionEvaluationDecision.PENDING: "Pending Review",
        }.get(decision, "Pending Review")

        subject = "Project Feedback - DevElan"
        body = (
            f"Hi {student_name},\n\n"
            f"Project: {project_title}\n"
            f"Evaluation: {decision_label}\n\n"
            "Feedback from Admin:\n"
            f"{feedback}\n\n"
            "Regards,\n"
            "DevElan Team"
        )
    else:
        subject = "Project Submission Received - DevElan"
        body = (
            f"Hi {student_name},\n\n"
            f"We have received your project '{project_title}'.\n"
            "Our team is reviewing your submission.\n\n"
            "Regards,\n"
            "DevElan Team"
        )

    return subject, body, SubmissionMailType.FEEDBACK


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


@router.patch("/update-evaluation", response_model=SubmissionEvaluationUpdateResponse)
def update_submission_evaluation(
    payload: SubmissionEvaluationUpdateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> SubmissionEvaluationUpdateResponse:
    submission = db.get(Submission, payload.submission_id)
    if submission is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found.",
        )

    evaluation = submission.evaluation
    if evaluation is None:
        evaluation = SubmissionEvaluation(submission_id=submission.id)

    feedback = payload.admin_feedback.strip() if isinstance(payload.admin_feedback, str) else ""
    evaluation.decision = payload.evaluation_decision
    evaluation.feedback = feedback or None

    db.add(evaluation)
    db.commit()
    db.refresh(evaluation)

    return SubmissionEvaluationUpdateResponse(
        success=True,
        submission_id=submission.id,
        evaluation_decision=evaluation.decision,
        admin_feedback=evaluation.feedback,
        message="Evaluation updated successfully.",
    )


@router.post("/send-evaluation-mail", response_model=SubmissionEvaluationMailResponse)
def send_submission_evaluation_mail(
    payload: SubmissionEvaluationMailRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> SubmissionEvaluationMailResponse:
    submission = db.get(Submission, payload.submission_id)
    if submission is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found.",
        )

    recipient_email = submission.user.email.strip() if submission.user.email else ""
    if not recipient_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student email is missing for this submission.",
        )

    evaluation = submission.evaluation
    mail_notification = submission.mail_notification
    if mail_notification is None:
        mail_notification = SubmissionMailNotification(submission_id=submission.id, sent_count=0)

    sent_count = int(mail_notification.sent_count or 0)
    if sent_count > 0 and not payload.send_anyway:
        return SubmissionEvaluationMailResponse(
            success=False,
            submission_id=submission.id,
            needs_confirmation=True,
            mail_type=mail_notification.last_mail_type,
            mail_sent_count=sent_count,
            last_mail_sent_at=mail_notification.last_sent_at,
            message="Mail already sent once. Send anyway?",
        )

    if sent_count == 0:
        subject, body, mail_type = _build_acceptance_mail_content(submission, evaluation)
    else:
        subject, body, mail_type = _build_feedback_mail_content(submission, evaluation)

    mail_result = send_submission_mail(
        recipient_email=recipient_email,
        subject=subject,
        body_text=body,
    )
    if not mail_result.success:
        logger.error(
            "Failed to send submission evaluation mail: submission_id=%s recipient=%s reason=%s",
            submission.id,
            recipient_email,
            mail_result.message,
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=mail_result.message,
        )

    now = datetime.now(UTC)
    if sent_count == 0 and mail_notification.first_sent_at is None:
        mail_notification.first_sent_at = now
    mail_notification.sent_count = sent_count + 1
    mail_notification.last_mail_type = mail_type
    mail_notification.last_sent_at = now

    db.add(mail_notification)
    db.commit()
    db.refresh(mail_notification)

    message = "Acceptance mail sent successfully." if mail_type == SubmissionMailType.ACCEPTANCE else "Feedback mail sent successfully."
    return SubmissionEvaluationMailResponse(
        success=True,
        submission_id=submission.id,
        needs_confirmation=False,
        mail_type=mail_type,
        mail_sent_count=mail_notification.sent_count,
        last_mail_sent_at=mail_notification.last_sent_at,
        message=message,
    )

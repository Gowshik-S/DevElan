from sqlalchemy import select
from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.submission import Submission
from app.models.usecase import UseCase, UseCaseAssignment
from app.models.user import User, UserRole
from app.schemas.usecase import UseCaseDetail, UseCaseListResponse, UseCaseSummary

router = APIRouter(prefix="/usecase", tags=["Use Case"])

NO_TASK_ASSIGNED_MESSAGE = "No task assigned yet. Stay ready — your next challenge is coming."


def _find_use_case(db: Session, use_case_id: str) -> UseCase | None:
    token = use_case_id.strip()
    if token.isdigit():
        return db.get(UseCase, int(token))
    return db.scalar(select(UseCase).where(UseCase.code.ilike(token)))


@router.get("/list", response_model=UseCaseListResponse)
def list_use_cases(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UseCaseListResponse:
    if current_user.role == UserRole.ADMIN:
        use_cases = db.scalars(select(UseCase).order_by(UseCase.code.asc())).all()
        return UseCaseListResponse(
            items=[
                UseCaseSummary(
                    id=use_case.id,
                    code=use_case.code,
                    title=use_case.title,
                    status=None,
                )
                for use_case in use_cases
            ],
            message=None,
        )

    assignments = db.scalars(
        select(UseCaseAssignment).where(UseCaseAssignment.user_id == current_user.id)
    ).all()
    if not assignments:
        return UseCaseListResponse(
            items=[],
            message=NO_TASK_ASSIGNED_MESSAGE,
        )

    submissions = db.scalars(
        select(Submission).where(Submission.user_id == current_user.id)
    ).all()
    status_by_use_case = {submission.usecase_id: submission.status for submission in submissions}

    response: list[UseCaseSummary] = []
    for assignment in assignments:
        use_case = assignment.usecase
        response.append(
            UseCaseSummary(
                id=use_case.id,
                code=use_case.code,
                title=use_case.title,
                status=status_by_use_case.get(use_case.id),
            )
        )
    return UseCaseListResponse(items=response, message=None)


@router.get("/get/{use_case_id}", response_model=UseCaseDetail)
def get_use_case_detail(
    use_case_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UseCaseDetail:
    use_case = _find_use_case(db, use_case_id)
    if use_case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Use case not found.",
        )

    user_status = None
    if current_user.role != UserRole.ADMIN:
        assignment = db.scalar(
            select(UseCaseAssignment).where(
                UseCaseAssignment.user_id == current_user.id,
                UseCaseAssignment.usecase_id == use_case.id,
            )
        )
        if assignment is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not assigned to this use case.",
            )

    submission = db.scalar(
        select(Submission).where(
            Submission.user_id == current_user.id,
            Submission.usecase_id == use_case.id,
        )
    )
    if submission is not None:
        user_status = submission.status

    return UseCaseDetail(
        id=use_case.id,
        code=use_case.code,
        title=use_case.title,
        description=use_case.description,
        key_concepts=use_case.key_concepts,
        workflow_steps=use_case.workflow_steps,
        output_description=use_case.output_description,
        status=user_status,
    )

from sqlalchemy import select
from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import ProfileResponse, ProfileUpdateRequest

router = APIRouter(prefix="/profile", tags=["Profile"])


def _build_profile_response(user: User) -> ProfileResponse:
    return ProfileResponse(
        id=user.id,
        full_name=user.full_name,
        register_no=user.register_no,
        email=user.email,
        class_name=user.class_name,
        dob=user.dob,
        year_semester=user.year_semester,
        phone=user.phone,
        role=user.role.value,
    )


@router.get("/get", response_model=ProfileResponse)
def get_profile(current_user: User = Depends(get_current_user)) -> ProfileResponse:
    return _build_profile_response(current_user)


@router.put("/update", response_model=ProfileResponse)
def update_profile(
    payload: ProfileUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProfileResponse:
    if payload.phone is not None:
        current_user.phone = payload.phone.strip() or None

    if payload.email is not None:
        normalized_email = payload.email.lower()
        existing = db.scalar(
            select(User).where(
                User.email == normalized_email,
                User.id != current_user.id,
            )
        )
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email address is already in use by another account.",
            )
        current_user.email = normalized_email

    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return _build_profile_response(current_user)

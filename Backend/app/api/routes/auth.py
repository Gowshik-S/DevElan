from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import get_current_user
from app.core.security import create_access_token, verify_password
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.auth import LoginRequest, LogoutResponse, TokenResponse

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    identifier = payload.login_id.strip()
    user = db.scalar(
        select(User).where(
            or_(
                User.register_no == identifier,
                User.email == identifier,
            )
        )
    )

    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid login credentials.",
        )

    access_token = create_access_token(subject=str(user.id), role=user.role.value)
    redirect_url = "/admin" if user.role == UserRole.ADMIN else "/user-home"

    return TokenResponse(
        access_token=access_token,
        user_id=user.id,
        user_role=user.role,
        redirect_url=redirect_url,
    )


@router.post("/logout", response_model=LogoutResponse)
def logout(_: User = Depends(get_current_user)) -> LogoutResponse:
    return LogoutResponse(success=True, message="Logout successful.")

from pydantic import BaseModel, Field

from app.models.user import UserRole


class LoginRequest(BaseModel):
    login_id: str = Field(min_length=3, max_length=120)
    password: str = Field(min_length=4, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    user_role: UserRole
    redirect_url: str


class LogoutResponse(BaseModel):
    success: bool
    message: str

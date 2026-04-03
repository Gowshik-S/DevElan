from datetime import date

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    register_no: str
    email: EmailStr
    class_name: str | None = None
    dob: date | None = None
    year_semester: str | None = None
    phone: str | None = None
    role: str


class ProfileUpdateRequest(BaseModel):
    phone: str | None = Field(default=None, max_length=25)
    email: EmailStr | None = None


class AdminUserCreateRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=150)
    register_no: str = Field(min_length=2, max_length=50)
    email: EmailStr
    class_assign: str = Field(min_length=1, max_length=80)


class AdminUserCreateResponse(BaseModel):
    user_id: int
    success: bool
    message: str
    temp_password: str

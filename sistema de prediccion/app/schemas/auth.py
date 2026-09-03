from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(
        min_length=8,
        max_length=128
    )


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    email: str
    is_active: bool

    model_config = {
        "from_attributes": True
    }


class UserProfileResponse(BaseModel):
    id: int
    email: str
    is_active: bool
    roles: list[str]

    model_config = {
        "from_attributes": True
    }


class SessionResponse(BaseModel):
    id: int
    session_uuid: str
    ip_address: str | None
    user_agent: str | None
    device_name: str | None
    is_active: bool
    created_at: datetime
    last_activity_at: datetime | None

    model_config = {
        "from_attributes": True
    }

class CurrentUserResponse(BaseModel):
    id: int
    email: str
    is_active: bool
    roles: list[str]
    permissions: list[str]
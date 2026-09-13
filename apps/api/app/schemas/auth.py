import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=1, max_length=255)
    clinic_name: str = Field(min_length=1, max_length=255)
    plan_key: str | None = Field(default=None, max_length=32)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AuthResponse(BaseModel):
    user_id: uuid.UUID
    email: EmailStr
    full_name: str
    clinic_id: uuid.UUID
    clinic_name: str
    organization_id: uuid.UUID | None = None
    organization_name: str | None = None
    role: str
    tokens: TokenPair


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=16)
    password: str = Field(min_length=8)


class VerifyEmailRequest(BaseModel):
    token: str = Field(min_length=16)


class SessionRead(BaseModel):
    id: uuid.UUID
    created_at: datetime
    expires_at: datetime
    is_current: bool = False

    model_config = {"from_attributes": True}


class ClinicMembershipRead(BaseModel):
    clinic_id: uuid.UUID
    clinic_name: str
    organization_id: uuid.UUID | None = None
    organization_name: str | None = None
    role: str
    is_active: bool

    model_config = {"from_attributes": True}


class OrganizationSummaryRead(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    status: str
    is_owner: bool = False


class ActiveClinicRead(BaseModel):
    id: uuid.UUID
    name: str
    role: str


class UserRead(BaseModel):
    id: uuid.UUID
    email: EmailStr
    full_name: str
    email_verified_at: datetime | None = None
    memberships: list[ClinicMembershipRead]
    organizations: list[OrganizationSummaryRead] = Field(default_factory=list)
    is_platform_admin: bool = False
    active_clinic: ActiveClinicRead | None = None
    permissions: list[str] = Field(default_factory=list)

    model_config = {"from_attributes": True}

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_db
from app.core.permissions import SETTINGS_ORGANIZATION, compute_permissions
from app.core.security import get_current_user
from app.models import Clinic, ClinicMembership, Organization, User
from app.schemas.auth import (
    ActiveClinicRead,
    AuthResponse,
    ForgotPasswordRequest,
    LoginRequest,
    LogoutRequest,
    OrganizationSummaryRead,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    SessionRead,
    TokenPair,
    UserRead,
    VerifyEmailRequest,
)
from app.services import account_service, auth_service, organization_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse)
async def register(
    data: RegisterRequest, db: Annotated[AsyncSession, Depends(get_db)]
) -> AuthResponse:
    return await auth_service.register_user(db, data)


@router.post("/login", response_model=AuthResponse)
async def login(data: LoginRequest, db: Annotated[AsyncSession, Depends(get_db)]) -> AuthResponse:
    return await auth_service.login_user(db, data)


@router.post("/refresh", response_model=TokenPair)
async def refresh(data: RefreshRequest, db: Annotated[AsyncSession, Depends(get_db)]) -> TokenPair:
    return await auth_service.refresh_tokens(db, data.refresh_token)


@router.post("/logout", status_code=204)
async def logout(data: LogoutRequest, db: Annotated[AsyncSession, Depends(get_db)]) -> None:
    await auth_service.logout_user(db, data.refresh_token)


@router.post("/forgot-password", status_code=204)
async def forgot_password(
    data: ForgotPasswordRequest, db: Annotated[AsyncSession, Depends(get_db)]
) -> None:
    await account_service.request_password_reset(db, data.email)


@router.post("/reset-password", status_code=204)
async def reset_password(
    data: ResetPasswordRequest, db: Annotated[AsyncSession, Depends(get_db)]
) -> None:
    await account_service.reset_password(db, data.token, data.password)


@router.post("/verify-email", status_code=204)
async def verify_email(
    data: VerifyEmailRequest, db: Annotated[AsyncSession, Depends(get_db)]
) -> None:
    await account_service.verify_email(db, data.token)


@router.post("/resend-verification", status_code=204)
async def resend_verification(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    await account_service.resend_verification(db, user)


@router.get("/sessions", response_model=list[SessionRead])
async def list_sessions(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[SessionRead]:
    rows = await account_service.list_sessions(db, user.id)
    return [SessionRead.model_validate(r) for r in rows]


@router.post("/logout-everywhere", status_code=204)
async def logout_everywhere(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    await account_service.logout_everywhere(db, user)


@router.get("/me", response_model=UserRead)
async def me(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    x_clinic_id: Annotated[str | None, Header(alias="X-Clinic-Id")] = None,
) -> UserRead:
    memberships = await auth_service.list_memberships(db, user.id)
    organizations = [
        OrganizationSummaryRead(**o.model_dump())
        for o in await organization_service.list_user_organizations(db, user)
    ]
    active_clinic = None
    permissions: list[str] = []

    if x_clinic_id:
        try:
            clinic_uuid = uuid.UUID(x_clinic_id)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid clinic id")

        result = await db.execute(
            select(ClinicMembership, Clinic)
            .join(Clinic, Clinic.id == ClinicMembership.clinic_id)
            .where(
                ClinicMembership.user_id == user.id,
                ClinicMembership.clinic_id == clinic_uuid,
                ClinicMembership.is_active.is_(True),
            )
        )
        row = result.one_or_none()
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "NO_ACTIVE_MEMBERSHIP", "message": "No active clinic membership"},
            )
        membership, clinic = row
        if getattr(clinic, "status", "active") == "suspended":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Clinic is suspended")

        active_clinic = {
            "id": clinic.id,
            "name": clinic.name,
            "role": membership.role,
        }
        permissions = compute_permissions(membership, clinic)
        if clinic.organization_id is not None:
            org = await db.get(Organization, clinic.organization_id)
            if org is not None and org.owner_id == user.id:
                if SETTINGS_ORGANIZATION not in permissions:
                    permissions = sorted([*permissions, SETTINGS_ORGANIZATION])

    return UserRead(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        email_verified_at=user.email_verified_at,
        memberships=memberships,
        organizations=organizations,
        is_platform_admin=user.email.lower() in settings.platform_admin_email_list,
        active_clinic=ActiveClinicRead(**active_clinic) if active_clinic else None,
        permissions=permissions,
    )

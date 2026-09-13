import uuid
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.models import ActivityLog, Clinic, ClinicMembership, Organization, RefreshToken, User
from app.schemas.auth import (
    AuthResponse,
    ClinicMembershipRead,
    LoginRequest,
    RegisterRequest,
    TokenPair,
)
from app.services.account_service import maybe_auto_verify, send_verification_email
from app.services.organization_service import (
    create_clinic_under_org,
    create_organization_with_subscription,
)


async def register_user(db: AsyncSession, data: RegisterRequest) -> AuthResponse:
    existing = await db.execute(select(User).where(User.email == data.email.lower()))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to create account with these details",
        )

    user = User(
        email=data.email.lower(),
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
    )
    plan_key = data.plan_key if data.plan_key in {"starter", "pro", "clinic"} else "starter"
    db.add(user)
    await db.flush()

    org = await create_organization_with_subscription(
        db,
        user,
        data.clinic_name,
        plan_key=plan_key,
        org_status="trial",
        sub_status="trial",
    )
    from app.schemas.organization import CreateClinicUnderOrgRequest

    clinic, _enrollment = await create_clinic_under_org(
        db,
        org,
        user,
        CreateClinicUnderOrgRequest(name=data.clinic_name),
        enrollment_status="active",
    )
    membership = await db.scalar(
        select(ClinicMembership).where(
            ClinicMembership.user_id == user.id,
            ClinicMembership.clinic_id == clinic.id,
        )
    )
    if membership is None:
        raise HTTPException(status_code=500, detail="Registration failed")
    maybe_auto_verify(user)
    if user.email_verified_at is None:
        await send_verification_email(db, user)
    tokens = await _issue_tokens(db, user)
    await db.commit()
    await db.refresh(user)
    return AuthResponse(
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        clinic_id=clinic.id,
        clinic_name=clinic.name,
        organization_id=org.id,
        organization_name=org.name,
        role="owner",
        tokens=tokens,
    )


async def login_user(db: AsyncSession, data: LoginRequest) -> AuthResponse:
    result = await db.execute(select(User).where(User.email == data.email.lower()))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account inactive")

    membership_result = await db.execute(
        select(ClinicMembership, Clinic)
        .join(Clinic, Clinic.id == ClinicMembership.clinic_id)
        .where(ClinicMembership.user_id == user.id, ClinicMembership.is_active.is_(True))
        .order_by(Clinic.name.asc(), ClinicMembership.created_at.asc())
        .limit(1)
    )
    row = membership_result.first()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="No active clinic membership"
        )

    membership, clinic = row
    tokens = await _issue_tokens(db, user)
    await db.commit()
    return AuthResponse(
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        clinic_id=clinic.id,
        clinic_name=clinic.name,
        role=membership.role,
        tokens=tokens,
    )


async def refresh_tokens(db: AsyncSession, raw_refresh: str) -> TokenPair:
    token_hash = hash_refresh_token(raw_refresh)
    result = await db.execute(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    stored = result.scalar_one_or_none()
    if stored is None or stored.revoked_at is not None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )
    if stored.expires_at < datetime.now(UTC):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired"
        )

    reuse_check = await db.execute(
        select(RefreshToken).where(
            RefreshToken.family_id == stored.family_id,
            RefreshToken.revoked_at.is_not(None),
            RefreshToken.created_at > stored.created_at,
        )
    )
    if reuse_check.first():
        await _revoke_token_family(db, stored.family_id)
        db.add(
            ActivityLog(
                clinic_id=None,
                actor_user_id=stored.user_id,
                actor_type="system",
                action="auth.refresh_token_reuse",
                target_type="user",
                target_id=str(stored.user_id),
                summary="Refresh token reuse detected; family revoked",
            )
        )
        await db.commit()
        from app.models import ClinicMembership
        from app.services.notification_service import notify_auth_refresh_reuse

        memberships = await db.execute(
            select(ClinicMembership).where(
                ClinicMembership.user_id == stored.user_id,
                ClinicMembership.is_active.is_(True),
            )
        )
        for membership in memberships.scalars().all():
            await notify_auth_refresh_reuse(
                db,
                clinic_id=membership.clinic_id,
                user_id=stored.user_id,
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )

    stored.revoked_at = datetime.now(UTC)
    user_result = await db.execute(select(User).where(User.id == stored.user_id))
    user = user_result.scalar_one()
    tokens = await _issue_tokens(db, user, family_id=stored.family_id)
    await db.commit()
    return tokens


async def logout_user(db: AsyncSession, raw_refresh: str) -> None:
    token_hash = hash_refresh_token(raw_refresh)
    result = await db.execute(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    stored = result.scalar_one_or_none()
    if stored and stored.revoked_at is None:
        stored.revoked_at = datetime.now(UTC)
        await db.commit()


async def _issue_tokens(
    db: AsyncSession, user: User, family_id: uuid.UUID | None = None
) -> TokenPair:
    raw_refresh = generate_refresh_token()
    family = family_id or uuid.uuid4()
    expires = datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=hash_refresh_token(raw_refresh),
            family_id=family,
            expires_at=expires,
            created_at=datetime.now(UTC),
        )
    )
    return TokenPair(access_token=create_access_token(user.id), refresh_token=raw_refresh)


async def _revoke_token_family(db: AsyncSession, family_id: uuid.UUID) -> None:
    result = await db.execute(select(RefreshToken).where(RefreshToken.family_id == family_id))
    for token in result.scalars():
        token.revoked_at = datetime.now(UTC)


async def list_memberships(db: AsyncSession, user_id: uuid.UUID) -> list[ClinicMembershipRead]:
    result = await db.execute(
        select(ClinicMembership, Clinic, Organization)
        .join(Clinic, Clinic.id == ClinicMembership.clinic_id)
        .outerjoin(Organization, Organization.id == Clinic.organization_id)
        .where(ClinicMembership.user_id == user_id)
        .order_by(Clinic.name.asc(), ClinicMembership.created_at.asc())
    )
    return [
        ClinicMembershipRead(
            clinic_id=m.clinic_id,
            clinic_name=c.name,
            organization_id=c.organization_id,
            organization_name=org.name if org else None,
            role=m.role,
            is_active=m.is_active,
        )
        for m, c, org in result.all()
    ]

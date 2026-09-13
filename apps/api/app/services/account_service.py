import os
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
)
from app.models import AccountToken, ActivityLog, RefreshToken, User
from app.services.email_service import send_account_email

RESET_TTL = timedelta(hours=1)
VERIFY_TTL = timedelta(hours=24)


def _testing() -> bool:
    return os.environ.get("DOCTORDESK_TESTING") == "1"


async def _issue_account_token(
    db: AsyncSession, user_id: uuid.UUID, purpose: str, ttl: timedelta
) -> str:
    await db.execute(
        update(AccountToken)
        .where(
            AccountToken.user_id == user_id,
            AccountToken.purpose == purpose,
            AccountToken.used_at.is_(None),
        )
        .values(used_at=datetime.now(UTC))
    )
    raw = generate_refresh_token()
    db.add(
        AccountToken(
            user_id=user_id,
            purpose=purpose,
            token_hash=hash_refresh_token(raw),
            expires_at=datetime.now(UTC) + ttl,
            created_at=datetime.now(UTC),
        )
    )
    await db.flush()
    return raw


async def _load_token(db: AsyncSession, raw: str, purpose: str) -> AccountToken:
    token_hash = hash_refresh_token(raw)
    result = await db.execute(
        select(AccountToken).where(
            AccountToken.token_hash == token_hash,
            AccountToken.purpose == purpose,
        )
    )
    row = result.scalar_one_or_none()
    if row is None or row.used_at is not None or row.expires_at < datetime.now(UTC):
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    return row


async def request_password_reset(db: AsyncSession, email: str) -> None:
    result = await db.execute(select(User).where(User.email == email.lower()))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        return
    raw = await _issue_account_token(db, user.id, "password_reset", RESET_TTL)
    url = f"{settings.web_base_url}/reset-password?token={raw}"
    send_account_email(
        user.email,
        "Reset your DoctorDesk password",
        f"Reset your password:\n\n{url}\n\nThis link expires in 1 hour.\n",
    )
    await db.commit()


async def reset_password(db: AsyncSession, raw_token: str, new_password: str) -> None:
    row = await _load_token(db, raw_token, "password_reset")
    user = await db.get(User, row.user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    user.hashed_password = hash_password(new_password)
    row.used_at = datetime.now(UTC)
    await revoke_all_sessions(db, user.id)
    db.add(
        ActivityLog(
            clinic_id=None,
            actor_user_id=user.id,
            actor_type="user",
            action="auth.password_reset",
            target_type="user",
            target_id=str(user.id),
            summary="Password reset completed",
        )
    )
    await db.commit()


async def send_verification_email(db: AsyncSession, user: User) -> None:
    if user.email_verified_at is not None:
        return
    raw = await _issue_account_token(db, user.id, "email_verify", VERIFY_TTL)
    url = f"{settings.web_base_url}/verify-email?token={raw}"
    send_account_email(
        user.email,
        "Verify your DoctorDesk email",
        f"Verify your email:\n\n{url}\n",
    )


async def verify_email(db: AsyncSession, raw_token: str) -> None:
    row = await _load_token(db, raw_token, "email_verify")
    user = await db.get(User, row.user_id)
    if user is None:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    user.email_verified_at = datetime.now(UTC)
    row.used_at = datetime.now(UTC)
    db.add(
        ActivityLog(
            clinic_id=None,
            actor_user_id=user.id,
            actor_type="user",
            action="auth.email_verified",
            target_type="user",
            target_id=str(user.id),
            summary="Email verified",
        )
    )
    await db.commit()


async def resend_verification(db: AsyncSession, user: User) -> None:
    if user.email_verified_at is not None:
        return
    await send_verification_email(db, user)
    await db.commit()


async def list_sessions(db: AsyncSession, user_id: uuid.UUID) -> list[RefreshToken]:
    result = await db.execute(
        select(RefreshToken)
        .where(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked_at.is_(None),
            RefreshToken.expires_at > datetime.now(UTC),
        )
        .order_by(RefreshToken.created_at.desc())
    )
    return list(result.scalars().all())


async def revoke_all_sessions(db: AsyncSession, user_id: uuid.UUID) -> int:
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked_at.is_(None),
        )
    )
    count = 0
    now = datetime.now(UTC)
    for token in result.scalars():
        token.revoked_at = now
        count += 1
    return count


async def logout_everywhere(db: AsyncSession, user: User) -> None:
    count = await revoke_all_sessions(db, user.id)
    db.add(
        ActivityLog(
            clinic_id=None,
            actor_user_id=user.id,
            actor_type="user",
            action="auth.logout_everywhere",
            target_type="user",
            target_id=str(user.id),
            summary="All sessions revoked",
            metadata_={"count": count},
        )
    )
    await db.commit()


def maybe_auto_verify(user: User) -> None:
    if _testing() and user.email_verified_at is None:
        user.email_verified_at = datetime.now(UTC)

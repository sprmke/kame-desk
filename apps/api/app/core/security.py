import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Annotated

import bcrypt
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_db
from app.models import Clinic, ClinicMembership, Patient, User

bearer_scheme = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(
    user_id: uuid.UUID,
    *,
    expires_minutes: int | None = None,
    extra_claims: dict | None = None,
) -> str:
    expire = datetime.now(UTC) + timedelta(
        minutes=expires_minutes or settings.access_token_expire_minutes
    )
    payload = {"sub": str(user_id), "exp": expire, "type": "access"}
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def create_patient_access_token(patient_id: uuid.UUID, clinic_id: uuid.UUID) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=settings.patient_access_token_expire_minutes)
    payload = {
        "sub": str(patient_id),
        "clinic_id": str(clinic_id),
        "exp": expire,
        "type": "patient_access",
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def hash_refresh_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def generate_refresh_token() -> str:
    return secrets.token_urlsafe(48)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        payload = jwt.decode(
            credentials.credentials, settings.secret_key, algorithms=[settings.algorithm]
        )
        if payload.get("type") != "access":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        user_id = uuid.UUID(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    result = await db.execute(select(User).where(User.id == user_id, User.is_active.is_(True)))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


async def get_active_clinic_membership(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    x_clinic_id: Annotated[str | None, Header(alias="X-Clinic-Id")] = None,
) -> ClinicMembership:
    if not x_clinic_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="X-Clinic-Id header required"
        )
    try:
        clinic_id = uuid.UUID(x_clinic_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid clinic id")

    result = await db.execute(
        select(ClinicMembership).where(
            ClinicMembership.user_id == user.id,
            ClinicMembership.clinic_id == clinic_id,
            ClinicMembership.is_active.is_(True),
        )
    )
    membership = result.scalar_one_or_none()
    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "NO_ACTIVE_MEMBERSHIP", "message": "No active clinic membership"},
        )
    clinic = await db.get(Clinic, membership.clinic_id)
    if clinic is not None and getattr(clinic, "status", "active") == "suspended":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Clinic is suspended")
    if clinic is not None and clinic.organization_id is not None:
        from app.models import Organization

        org = await db.get(Organization, clinic.organization_id)
        if org is not None and org.status == "suspended":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Organization is suspended"
            )
    return membership


async def get_current_patient(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Patient:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        payload = jwt.decode(
            credentials.credentials, settings.secret_key, algorithms=[settings.algorithm]
        )
        if payload.get("type") != "patient_access":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        patient_id = uuid.UUID(payload["sub"])
        clinic_id = uuid.UUID(payload["clinic_id"])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    result = await db.execute(
        select(Patient).where(
            Patient.id == patient_id,
            Patient.clinic_id == clinic_id,
            Patient.is_archived.is_(False),
        )
    )
    patient = result.scalar_one_or_none()
    if patient is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Patient not found")
    return patient


async def get_user_from_access_token(token: str, db: AsyncSession) -> User:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        if payload.get("type") != "access":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        user_id = uuid.UUID(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    result = await db.execute(select(User).where(User.id == user_id, User.is_active.is_(True)))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


async def verify_clinic_membership(
    user: User, clinic_id: uuid.UUID, db: AsyncSession
) -> ClinicMembership:
    result = await db.execute(
        select(ClinicMembership).where(
            ClinicMembership.user_id == user.id,
            ClinicMembership.clinic_id == clinic_id,
            ClinicMembership.is_active.is_(True),
        )
    )
    membership = result.scalar_one_or_none()
    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "NO_ACTIVE_MEMBERSHIP", "message": "No active clinic membership"},
        )
    return membership


def require_clinic_role(*roles: str):
    async def _checker(
        membership: Annotated[ClinicMembership, Depends(get_active_clinic_membership)],
    ) -> ClinicMembership:
        if membership.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
        return membership

    return _checker

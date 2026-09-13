import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import get_current_user
from app.models import OrganizationEnrolledClinic, OrganizationSubscription, User
from app.services import platform_service

router = APIRouter(prefix="/platform", tags=["platform"])


class TenantPatch(BaseModel):
    status: str | None = None
    plan_key: str | None = None


class EnrollmentPatch(BaseModel):
    status: str


class FlagPatch(BaseModel):
    enabled: bool


async def _admin(
    user: Annotated[User, Depends(get_current_user)],
) -> User:
    platform_service.assert_platform_admin(user)
    return user


@router.get("/plans")
async def list_plans(_user: Annotated[User, Depends(_admin)]) -> list[dict]:
    return list(platform_service.PLANS)


@router.get("/tenants")
async def list_tenants(
    _user: Annotated[User, Depends(_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    q: str | None = None,
) -> list[dict]:
    rows = await platform_service.list_org_tenants(db, q)
    out: list[dict] = []
    for org in rows:
        clinic_count = await db.scalar(
            select(func.count())
            .select_from(OrganizationEnrolledClinic)
            .where(OrganizationEnrolledClinic.organization_id == org.id)
        )
        sub = org.subscription
        out.append(
            {
                "id": str(org.id),
                "name": org.name,
                "slug": org.slug,
                "status": org.status,
                "plan_key": sub.plan_key if sub else "starter",
                "clinic_count": int(clinic_count or 0),
                "tenant_type": "organization",
            }
        )
    return out


@router.get("/tenants/{org_id}")
async def get_tenant(
    org_id: uuid.UUID,
    _user: Annotated[User, Depends(_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    org = await platform_service.get_org_tenant_detail(db, org_id)
    sub = org.subscription
    enrollments = []
    for row in org.enrolled_clinics:
        clinic = row.clinic
        enrollments.append(
            {
                "id": str(row.id),
                "clinic_id": str(row.clinic_id),
                "clinic_name": clinic.name if clinic else "",
                "clinic_slug": clinic.slug if clinic else "",
                "status": row.status,
                "enrolled_at": row.enrolled_at.isoformat() if row.enrolled_at else None,
            }
        )
    return {
        "id": str(org.id),
        "name": org.name,
        "slug": org.slug,
        "status": org.status,
        "plan_key": sub.plan_key if sub else "starter",
        "subscription_status": sub.status if sub else "trial",
        "enrollments": enrollments,
    }


@router.patch("/tenants/{org_id}")
async def patch_tenant(
    org_id: uuid.UUID,
    data: TenantPatch,
    user: Annotated[User, Depends(_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    org = await platform_service.patch_org_tenant(
        db, org_id, user.id, status=data.status, plan_key=data.plan_key
    )
    sub = await db.scalar(
        select(OrganizationSubscription).where(OrganizationSubscription.organization_id == org.id)
    )
    return {
        "id": str(org.id),
        "name": org.name,
        "status": org.status,
        "plan_key": sub.plan_key if sub else "starter",
    }


@router.patch("/tenants/{org_id}/enrollments/{clinic_id}")
async def patch_enrollment(
    org_id: uuid.UUID,
    clinic_id: uuid.UUID,
    data: EnrollmentPatch,
    user: Annotated[User, Depends(_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    enrollment = await platform_service.patch_enrollment(
        db, org_id, clinic_id, user.id, status=data.status
    )
    return {
        "id": str(enrollment.id),
        "clinic_id": str(enrollment.clinic_id),
        "status": enrollment.status,
        "enrolled_at": enrollment.enrolled_at.isoformat() if enrollment.enrolled_at else None,
    }


@router.patch("/tenants/clinic/{clinic_id}")
async def patch_clinic_tenant_legacy(
    clinic_id: uuid.UUID,
    data: TenantPatch,
    user: Annotated[User, Depends(_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    clinic = await platform_service.patch_tenant(
        db, clinic_id, user.id, status=data.status, plan_key=data.plan_key
    )
    return {
        "id": str(clinic.id),
        "name": clinic.name,
        "status": clinic.status,
        "plan_key": clinic.plan_key,
    }


@router.post("/tenants/{org_id}/impersonate")
async def impersonate(
    org_id: uuid.UUID,
    user: Annotated[User, Depends(_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    return await platform_service.impersonate_org_owner(db, org_id, user)


@router.post("/tenants/clinic/{clinic_id}/impersonate")
async def impersonate_clinic_legacy(
    clinic_id: uuid.UUID,
    user: Annotated[User, Depends(_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    return await platform_service.impersonate_owner(db, clinic_id, user)


@router.get("/flags/{key}")
async def get_flag(
    key: str,
    _user: Annotated[User, Depends(_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    from app.models import PlatformFeatureFlag

    flag = await db.get(PlatformFeatureFlag, key)
    return {"key": key, "enabled": bool(flag.enabled) if flag else False}


@router.patch("/flags/{key}")
async def patch_flag(
    key: str,
    data: FlagPatch,
    user: Annotated[User, Depends(_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    flag = await platform_service.set_flag(db, user.id, key, data.enabled)
    return {"key": flag.key, "enabled": flag.enabled}


@router.get("/metrics")
async def metrics(
    _user: Annotated[User, Depends(_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    return await platform_service.platform_metrics(db)


@router.get("/audit")
async def platform_audit(
    _user: Annotated[User, Depends(_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[dict]:
    from sqlalchemy import select

    from app.models import PlatformAuditLog

    result = await db.execute(
        select(PlatformAuditLog).order_by(PlatformAuditLog.created_at.desc()).limit(100)
    )
    return [
        {
            "id": str(row.id),
            "action": row.action,
            "summary": row.summary,
            "target_type": row.target_type,
            "target_id": row.target_id,
            "created_at": row.created_at.isoformat(),
        }
        for row in result.scalars().all()
    ]

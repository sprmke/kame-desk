import uuid
from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.security import create_access_token
from app.models import (
    Appointment,
    Clinic,
    ClinicAiUsage,
    ClinicMembership,
    Organization,
    OrganizationEnrolledClinic,
    OrganizationSubscription,
    PatientFile,
    PlatformAuditLog,
    PlatformFeatureFlag,
    Reminder,
    User,
)

PLANS = (
    {
        "key": "starter",
        "name": "Starter",
        "monthly_php": 1990,
        "trial_days": 14,
        "included": "1 doctor, 1 clinic, email reminders",
    },
    {
        "key": "pro",
        "name": "Pro",
        "monthly_php": 4990,
        "trial_days": 14,
        "included": "5 doctors, 3 clinics, SMS metered, AI cap 300/day",
    },
    {
        "key": "clinic",
        "name": "Clinic",
        "monthly_php": 9990,
        "trial_days": 14,
        "included": "Unlimited doctors and clinics, higher AI cap",
    },
)

PLAN_ENTITLEMENTS: dict[str, dict[str, int | None]] = {
    "starter": {"doctor_seats": 1, "max_clinics": 1},
    "pro": {"doctor_seats": 5, "max_clinics": 3},
    "clinic": {"doctor_seats": None, "max_clinics": None},
}


def assert_platform_admin(user: User) -> None:
    if user.email.lower() not in settings.platform_admin_email_list:
        raise HTTPException(status_code=403, detail="Platform admin only")


async def log_platform(
    db: AsyncSession,
    actor_id: uuid.UUID,
    action: str,
    summary: str,
    *,
    target_type: str | None = None,
    target_id: str | None = None,
) -> None:
    db.add(
        PlatformAuditLog(
            actor_user_id=actor_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            summary=summary,
            created_at=datetime.now(UTC),
        )
    )


async def list_org_tenants(db: AsyncSession, q: str | None = None) -> list[Organization]:
    query = (
        select(Organization)
        .options(selectinload(Organization.subscription))
        .order_by(Organization.created_at.desc())
    )
    if q:
        query = query.where(Organization.name.ilike(f"%{q.strip()}%"))
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_org_tenant_detail(db: AsyncSession, org_id: uuid.UUID) -> Organization:
    result = await db.execute(
        select(Organization)
        .options(
            selectinload(Organization.subscription),
            selectinload(Organization.enrolled_clinics).selectinload(
                OrganizationEnrolledClinic.clinic
            ),
        )
        .where(Organization.id == org_id)
    )
    org = result.scalar_one_or_none()
    if org is None:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org


async def patch_org_tenant(
    db: AsyncSession,
    org_id: uuid.UUID,
    actor_id: uuid.UUID,
    *,
    status: str | None = None,
    plan_key: str | None = None,
) -> Organization:
    org = await db.get(Organization, org_id)
    if org is None:
        raise HTTPException(status_code=404, detail="Organization not found")
    if status:
        if status not in ("trial", "active", "suspended", "cancelled"):
            raise HTTPException(status_code=400, detail="Invalid status")
        org.status = status
    sub = await db.scalar(
        select(OrganizationSubscription).where(OrganizationSubscription.organization_id == org_id)
    )
    if plan_key:
        if plan_key not in {p["key"] for p in PLANS}:
            raise HTTPException(status_code=400, detail="Invalid plan")
        if sub is None:
            sub = OrganizationSubscription(organization_id=org_id, plan_key=plan_key)
            db.add(sub)
        else:
            sub.plan_key = plan_key
    if sub and status:
        sub.status = status
    await log_platform(
        db,
        actor_id,
        "org.updated",
        "Organization updated",
        target_type="organization",
        target_id=str(org.id),
    )
    await db.commit()
    await db.refresh(org)
    return org


async def patch_enrollment(
    db: AsyncSession,
    org_id: uuid.UUID,
    clinic_id: uuid.UUID,
    actor_id: uuid.UUID,
    *,
    status: str,
) -> OrganizationEnrolledClinic:
    if status not in ("pending_enrollment", "active", "deactivated"):
        raise HTTPException(status_code=400, detail="Invalid enrollment status")
    result = await db.execute(
        select(OrganizationEnrolledClinic).where(
            OrganizationEnrolledClinic.organization_id == org_id,
            OrganizationEnrolledClinic.clinic_id == clinic_id,
        )
    )
    enrollment = result.scalar_one_or_none()
    if enrollment is None:
        raise HTTPException(status_code=404, detail="Enrollment not found")
    enrollment.status = status
    if status == "active":
        enrollment.enrolled_at = datetime.now(UTC)
    await log_platform(
        db,
        actor_id,
        "org.enrollment.updated",
        f"Enrollment set to {status}",
        target_type="organization_enrolled_clinic",
        target_id=str(enrollment.id),
    )
    await db.commit()
    await db.refresh(enrollment)
    return enrollment


async def list_tenants(db: AsyncSession, q: str | None = None) -> list[Clinic]:
    query = select(Clinic).order_by(Clinic.created_at.desc())
    if q:
        query = query.where(Clinic.name.ilike(f"%{q.strip()}%"))
    result = await db.execute(query)
    return list(result.scalars().all())


async def patch_tenant(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    actor_id: uuid.UUID,
    *,
    status: str | None = None,
    plan_key: str | None = None,
) -> Clinic:
    clinic = await db.get(Clinic, clinic_id)
    if clinic is None:
        raise HTTPException(status_code=404, detail="Clinic not found")
    if clinic.organization_id:
        await patch_org_tenant(
            db, clinic.organization_id, actor_id, status=status, plan_key=plan_key
        )
        await db.refresh(clinic)
        return clinic
    if status:
        if status not in ("trial", "active", "suspended", "cancelled"):
            raise HTTPException(status_code=400, detail="Invalid status")
        clinic.status = status
    if plan_key:
        if plan_key not in {p["key"] for p in PLANS}:
            raise HTTPException(status_code=400, detail="Invalid plan")
        clinic.plan_key = plan_key
    await log_platform(
        db,
        actor_id,
        "tenant.updated",
        "Tenant updated",
        target_type="clinic",
        target_id=str(clinic.id),
    )
    await db.commit()
    await db.refresh(clinic)
    return clinic


async def set_flag(
    db: AsyncSession, actor_id: uuid.UUID, key: str, enabled: bool
) -> PlatformFeatureFlag:
    flag = await db.get(PlatformFeatureFlag, key)
    if flag is None:
        flag = PlatformFeatureFlag(key=key, enabled=enabled, updated_at=datetime.now(UTC))
        db.add(flag)
    else:
        flag.enabled = enabled
        flag.updated_at = datetime.now(UTC)
    await log_platform(
        db,
        actor_id,
        "flag.updated",
        f"Flag {key} set to {enabled}",
        target_type="feature_flag",
        target_id=key,
    )
    await db.commit()
    await db.refresh(flag)
    return flag


async def impersonate_org_owner(db: AsyncSession, org_id: uuid.UUID, actor: User) -> dict:
    org = await db.get(Organization, org_id)
    if org is None:
        raise HTTPException(status_code=404, detail="Organization not found")
    owner = await db.get(User, org.owner_id)
    if owner is None:
        raise HTTPException(status_code=404, detail="Owner not found")

    clinic_result = await db.execute(
        select(Clinic)
        .join(
            OrganizationEnrolledClinic,
            OrganizationEnrolledClinic.clinic_id == Clinic.id,
        )
        .where(OrganizationEnrolledClinic.organization_id == org_id)
        .order_by(Clinic.created_at.asc())
        .limit(1)
    )
    clinic = clinic_result.scalar_one_or_none()
    if clinic is None:
        clinic_result = await db.execute(
            select(Clinic).where(Clinic.organization_id == org_id).limit(1)
        )
        clinic = clinic_result.scalar_one_or_none()
    if clinic is None:
        raise HTTPException(status_code=404, detail="No clinic found for organization")

    access = create_access_token(
        owner.id,
        expires_minutes=30,
        extra_claims={"imp": True, "imp_by": str(actor.id)},
    )
    await log_platform(
        db,
        actor.id,
        "org.impersonated",
        "Support login started",
        target_type="organization",
        target_id=str(org_id),
    )
    await db.commit()
    return {
        "organization_id": str(org_id),
        "clinic_id": str(clinic.id),
        "access_token": access,
        "impersonated_user_id": str(owner.id),
        "expires_minutes": 30,
    }


async def impersonate_owner(db: AsyncSession, clinic_id: uuid.UUID, actor: User) -> dict:
    clinic = await db.get(Clinic, clinic_id)
    if clinic is not None and clinic.organization_id:
        return await impersonate_org_owner(db, clinic.organization_id, actor)

    result = await db.execute(
        select(ClinicMembership).where(
            ClinicMembership.clinic_id == clinic_id,
            ClinicMembership.role == "owner",
            ClinicMembership.is_active.is_(True),
        )
    )
    membership = result.scalar_one_or_none()
    if membership is None:
        raise HTTPException(status_code=404, detail="Owner membership not found")
    owner = await db.get(User, membership.user_id)
    if owner is None:
        raise HTTPException(status_code=404, detail="Owner not found")
    access = create_access_token(
        owner.id,
        expires_minutes=30,
        extra_claims={"imp": True, "imp_by": str(actor.id)},
    )
    await log_platform(
        db,
        actor.id,
        "tenant.impersonated",
        "Support login started",
        target_type="clinic",
        target_id=str(clinic_id),
    )
    await db.commit()
    return {
        "clinic_id": str(clinic_id),
        "access_token": access,
        "impersonated_user_id": str(owner.id),
        "expires_minutes": 30,
    }


async def platform_metrics(db: AsyncSession) -> dict:
    orgs = await db.execute(select(Organization.status, func.count()).group_by(Organization.status))
    orgs_by_status = {row[0]: int(row[1]) for row in orgs.all()}
    clinics = await db.execute(select(Clinic.status, func.count()).group_by(Clinic.status))
    by_status = {row[0]: int(row[1]) for row in clinics.all()}
    appts = await db.execute(select(func.count()).select_from(Appointment))
    ai = await db.execute(
        select(
            func.coalesce(func.sum(ClinicAiUsage.request_count), 0),
            func.coalesce(func.sum(ClinicAiUsage.token_count), 0),
        )
    )
    ai_requests, ai_tokens = ai.one()
    sms_sent = await db.execute(
        select(func.count())
        .select_from(Reminder)
        .where(Reminder.channel == "sms", Reminder.status == "sent")
    )
    sms_failed = await db.execute(
        select(func.count())
        .select_from(Reminder)
        .where(Reminder.channel == "sms", Reminder.status == "failed")
    )
    files = await db.execute(select(func.count()).select_from(PatientFile))
    per_clinic = await db.execute(
        select(
            Clinic.id,
            Clinic.name,
            func.coalesce(func.sum(ClinicAiUsage.request_count), 0),
        )
        .outerjoin(ClinicAiUsage, ClinicAiUsage.clinic_id == Clinic.id)
        .group_by(Clinic.id, Clinic.name)
        .order_by(func.coalesce(func.sum(ClinicAiUsage.request_count), 0).desc())
        .limit(20)
    )
    return {
        "organizations_by_status": orgs_by_status,
        "clinics_by_status": by_status,
        "appointments_total": int(appts.scalar_one() or 0),
        "ai_requests": int(ai_requests or 0),
        "ai_tokens": int(ai_tokens or 0),
        "sms_sent": int(sms_sent.scalar_one() or 0),
        "sms_failed": int(sms_failed.scalar_one() or 0),
        "files_total": int(files.scalar_one() or 0),
        "clinics_by_ai_requests": [
            {
                "clinic_id": str(row[0]),
                "name": row[1],
                "ai_requests": int(row[2]),
            }
            for row in per_clinic.all()
        ],
    }

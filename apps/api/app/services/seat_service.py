import uuid

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Clinic,
    ClinicMembership,
    OrganizationEnrolledClinic,
    StaffInvitation,
)
from app.services.organization_service import (
    get_org_for_clinic,
    get_org_subscription,
    resolve_plan_key,
)
from app.services.platform_service import PLAN_ENTITLEMENTS

PLAN_DOCTOR_SEAT_LIMITS: dict[str, int | None] = {
    "starter": 1,
    "pro": 5,
    "clinic": None,
}


def doctor_seat_limit_for_plan(plan_key: str) -> int | None:
    entitlements = PLAN_ENTITLEMENTS.get(plan_key, PLAN_ENTITLEMENTS["starter"])
    seats = entitlements.get("doctor_seats")
    if seats is not None:
        return int(seats)
    return PLAN_DOCTOR_SEAT_LIMITS.get(plan_key, 1)


async def _enrolled_clinic_ids(db: AsyncSession, org_id: uuid.UUID) -> list[uuid.UUID]:
    result = await db.execute(
        select(OrganizationEnrolledClinic.clinic_id).where(
            OrganizationEnrolledClinic.organization_id == org_id,
            OrganizationEnrolledClinic.status == "active",
        )
    )
    return [row[0] for row in result.all()]


async def count_doctor_seats_used_org(db: AsyncSession, org_id: uuid.UUID) -> int:
    clinic_ids = await _enrolled_clinic_ids(db, org_id)
    if not clinic_ids:
        return 0

    active_doctors = await db.scalar(
        select(func.count())
        .select_from(ClinicMembership)
        .where(
            ClinicMembership.clinic_id.in_(clinic_ids),
            ClinicMembership.is_active.is_(True),
            ClinicMembership.role == "doctor",
        )
    )
    pending_doctor_invites = await db.scalar(
        select(func.count())
        .select_from(StaffInvitation)
        .where(
            StaffInvitation.clinic_id.in_(clinic_ids),
            StaffInvitation.role == "doctor",
            StaffInvitation.accepted_at.is_(None),
            StaffInvitation.revoked_at.is_(None),
        )
    )
    return int(active_doctors or 0) + int(pending_doctor_invites or 0)


async def count_doctor_seats_used(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    *,
    exclude_invitation_id: uuid.UUID | None = None,
) -> int:
    clinic = await db.get(Clinic, clinic_id)
    if clinic is None or clinic.organization_id is None:
        clinic_ids = [clinic_id]
    else:
        org = await get_org_for_clinic(db, clinic_id)
        clinic_ids = await _enrolled_clinic_ids(db, org.id)
        if not clinic_ids:
            clinic_ids = [clinic_id]

    active_doctors = await db.scalar(
        select(func.count())
        .select_from(ClinicMembership)
        .where(
            ClinicMembership.clinic_id.in_(clinic_ids),
            ClinicMembership.is_active.is_(True),
            ClinicMembership.role == "doctor",
        )
    )
    pending_query = (
        select(func.count())
        .select_from(StaffInvitation)
        .where(
            StaffInvitation.clinic_id.in_(clinic_ids),
            StaffInvitation.role == "doctor",
            StaffInvitation.accepted_at.is_(None),
            StaffInvitation.revoked_at.is_(None),
        )
    )
    if exclude_invitation_id is not None:
        pending_query = pending_query.where(StaffInvitation.id != exclude_invitation_id)
    pending_doctor_invites = await db.scalar(pending_query)
    return int(active_doctors or 0) + int(pending_doctor_invites or 0)


async def doctor_seat_limit_for_clinic(db: AsyncSession, clinic_id: uuid.UUID) -> int | None:
    clinic = await db.get(Clinic, clinic_id)
    if clinic is None:
        return 1
    if clinic.organization_id is None:
        return doctor_seat_limit(clinic)
    org = await get_org_for_clinic(db, clinic_id)
    sub = await get_org_subscription(db, org.id)
    plan_key = resolve_plan_key(sub, clinic)
    return doctor_seat_limit_for_plan(plan_key)


def doctor_seat_limit(clinic: Clinic) -> int | None:
    if clinic.plan_key:
        return doctor_seat_limit_for_plan(clinic.plan_key)
    return PLAN_DOCTOR_SEAT_LIMITS.get("starter", 1)


async def assert_doctor_seat_available(
    db: AsyncSession,
    clinic: Clinic,
    *,
    exclude_invitation_id: uuid.UUID | None = None,
) -> None:
    from app.services.organization_service import get_enrollment_for_clinic

    enrollment = await get_enrollment_for_clinic(db, clinic.id)
    if enrollment is not None and enrollment.status != "active":
        raise HTTPException(
            status_code=409,
            detail="Doctor invites are unavailable until clinic enrollment is active",
        )

    limit = await doctor_seat_limit_for_clinic(db, clinic.id)
    if limit is None:
        return
    used = await count_doctor_seats_used(db, clinic.id, exclude_invitation_id=exclude_invitation_id)
    if used >= limit:
        sub = (
            await get_org_subscription(db, clinic.organization_id)
            if clinic.organization_id
            else None
        )
        plan_key = resolve_plan_key(sub, clinic)
        raise HTTPException(
            status_code=409,
            detail=f"Doctor seat limit reached for the {plan_key} plan",
        )


async def seat_summary(db: AsyncSession, clinic: Clinic) -> dict[str, int | None]:
    limit = await doctor_seat_limit_for_clinic(db, clinic.id)
    used = await count_doctor_seats_used(db, clinic.id)
    remaining = None if limit is None else max(limit - used, 0)
    return {"limit": limit, "used": used, "remaining": remaining}


async def org_seat_summary(db: AsyncSession, org_id: uuid.UUID) -> dict[str, int | None]:
    from app.services.platform_service import PLAN_ENTITLEMENTS

    sub = await get_org_subscription(db, org_id)
    plan_key = sub.plan_key if sub else "starter"
    limit = doctor_seat_limit_for_plan(plan_key)
    used = await count_doctor_seats_used_org(db, org_id)
    remaining = None if limit is None else max(limit - used, 0)
    max_clinics = PLAN_ENTITLEMENTS.get(plan_key, PLAN_ENTITLEMENTS["starter"]).get("max_clinics")
    enrolled = await db.scalar(
        select(func.count())
        .select_from(OrganizationEnrolledClinic)
        .where(
            OrganizationEnrolledClinic.organization_id == org_id,
            OrganizationEnrolledClinic.status.in_(("active", "pending_enrollment")),
        )
    )
    return {
        "limit": limit,
        "used": used,
        "remaining": remaining,
        "max_clinics": max_clinics,
        "enrolled_clinics": int(enrolled or 0),
    }

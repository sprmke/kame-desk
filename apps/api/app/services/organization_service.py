import uuid
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import (
    ActivityLog,
    Clinic,
    ClinicMembership,
    Organization,
    OrganizationEnrolledClinic,
    OrganizationSubscription,
    User,
)
from app.schemas.organization import (
    CreateClinicUnderOrgRequest,
    EnrolledClinicRead,
    OrganizationDetailRead,
    OrganizationRead,
    OrganizationSubscriptionRead,
)
from app.services.org_slug_service import ensure_unique_org_slug, org_slug_from_name
from app.services.platform_service import PLAN_ENTITLEMENTS, PLANS
from app.services.slug_service import ensure_unique_slug, slugify_name


async def get_organization(db: AsyncSession, org_id: uuid.UUID) -> Organization:
    org = await db.get(Organization, org_id)
    if org is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    return org


async def get_org_for_clinic(db: AsyncSession, clinic_id: uuid.UUID) -> Organization:
    clinic = await db.get(Clinic, clinic_id)
    if clinic is None or clinic.organization_id is None:
        raise HTTPException(status_code=404, detail="Organization not found for clinic")
    return await get_organization(db, clinic.organization_id)


async def get_org_subscription(
    db: AsyncSession, org_id: uuid.UUID
) -> OrganizationSubscription | None:
    result = await db.execute(
        select(OrganizationSubscription).where(OrganizationSubscription.organization_id == org_id)
    )
    return result.scalar_one_or_none()


def resolve_plan_key(subscription: OrganizationSubscription | None, clinic: Clinic | None) -> str:
    if subscription is not None:
        return subscription.plan_key
    if clinic is not None and clinic.plan_key:
        return clinic.plan_key
    return "starter"


async def user_can_access_org(db: AsyncSession, user: User, org_id: uuid.UUID) -> bool:
    org = await db.get(Organization, org_id)
    if org is None:
        return False
    if org.owner_id == user.id:
        return True
    result = await db.execute(
        select(ClinicMembership.id)
        .join(Clinic, Clinic.id == ClinicMembership.clinic_id)
        .where(
            Clinic.organization_id == org_id,
            ClinicMembership.user_id == user.id,
            ClinicMembership.is_active.is_(True),
        )
        .limit(1)
    )
    return result.scalar_one_or_none() is not None


async def assert_org_owner(db: AsyncSession, user: User, org_id: uuid.UUID) -> Organization:
    org = await get_organization(db, org_id)
    if org.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Organization owner only")
    return org


async def create_organization_with_subscription(
    db: AsyncSession,
    owner: User,
    name: str,
    *,
    plan_key: str = "starter",
    org_status: str = "trial",
    sub_status: str = "trial",
    trial_days: int = 14,
) -> Organization:
    if plan_key not in {p["key"] for p in PLANS}:
        plan_key = "starter"
    base_slug = await ensure_unique_org_slug(db, org_slug_from_name(name))
    org = Organization(
        owner_id=owner.id,
        name=name,
        slug=base_slug,
        status=org_status,
    )
    db.add(org)
    await db.flush()
    sub = OrganizationSubscription(
        organization_id=org.id,
        plan_key=plan_key,
        status=sub_status,
        trial_ends_at=datetime.now(UTC) + timedelta(days=trial_days),
    )
    db.add(sub)
    await db.flush()
    return org


async def create_clinic_under_org(
    db: AsyncSession,
    org: Organization,
    owner: User,
    data: CreateClinicUnderOrgRequest,
    *,
    enrollment_status: str = "pending_enrollment",
) -> tuple[Clinic, OrganizationEnrolledClinic]:
    if org.status == "cancelled":
        raise HTTPException(status_code=409, detail="Organization is cancelled")

    sub = await get_org_subscription(db, org.id)
    plan_key = resolve_plan_key(sub, None)
    entitlements = PLAN_ENTITLEMENTS.get(plan_key, PLAN_ENTITLEMENTS["starter"])
    max_clinics = entitlements.get("max_clinics")
    if max_clinics is not None:
        active_count = await db.scalar(
            select(func.count())
            .select_from(OrganizationEnrolledClinic)
            .where(
                OrganizationEnrolledClinic.organization_id == org.id,
                OrganizationEnrolledClinic.status.in_(("active", "pending_enrollment")),
            )
        )
        if int(active_count or 0) >= max_clinics:
            raise HTTPException(
                status_code=409,
                detail=f"Clinic limit reached for the {plan_key} plan",
            )

    base_slug = slugify_name(data.slug or data.name)
    clinic_slug = await ensure_unique_slug(db, base_slug)
    clinic = Clinic(
        name=data.name,
        slug=clinic_slug,
        organization_id=org.id,
        status="active",
    )
    db.add(clinic)
    await db.flush()

    membership = ClinicMembership(
        user_id=owner.id,
        clinic_id=clinic.id,
        role="owner",
        is_active=True,
    )
    db.add(membership)

    enrolled_at = datetime.now(UTC) if enrollment_status == "active" else None
    enrollment = OrganizationEnrolledClinic(
        organization_id=org.id,
        clinic_id=clinic.id,
        status=enrollment_status,
        enrolled_at=enrolled_at,
    )
    db.add(enrollment)

    db.add(
        ActivityLog(
            clinic_id=clinic.id,
            actor_user_id=owner.id,
            actor_type="user",
            action="clinic.created",
            target_type="clinic",
            target_id=str(clinic.id),
            summary=f"Clinic created under organization {org.name}",
            metadata_={"organization_id": str(org.id)},
        )
    )
    await db.flush()
    return clinic, enrollment


async def list_user_organizations(db: AsyncSession, user: User) -> list[OrganizationRead]:
    owned = await db.execute(
        select(Organization).where(Organization.owner_id == user.id).order_by(Organization.name)
    )
    results: dict[uuid.UUID, OrganizationRead] = {}
    for org in owned.scalars():
        results[org.id] = OrganizationRead(
            id=org.id,
            name=org.name,
            slug=org.slug,
            status=org.status,
            is_owner=True,
        )

    member_orgs = await db.execute(
        select(Organization)
        .join(Clinic, Clinic.organization_id == Organization.id)
        .join(ClinicMembership, ClinicMembership.clinic_id == Clinic.id)
        .where(
            ClinicMembership.user_id == user.id,
            ClinicMembership.is_active.is_(True),
            Organization.owner_id != user.id,
        )
        .distinct()
        .order_by(Organization.name)
    )
    for org in member_orgs.scalars():
        if org.id not in results:
            results[org.id] = OrganizationRead(
                id=org.id,
                name=org.name,
                slug=org.slug,
                status=org.status,
                is_owner=False,
            )
    return sorted(results.values(), key=lambda o: o.name.lower())


async def get_organization_detail(
    db: AsyncSession, org_id: uuid.UUID, user: User
) -> OrganizationDetailRead:
    if not await user_can_access_org(db, user, org_id):
        raise HTTPException(status_code=403, detail="No access to organization")

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

    sub_read = None
    if org.subscription:
        sub_read = OrganizationSubscriptionRead.model_validate(org.subscription)

    enrolled: list[EnrolledClinicRead] = []
    for row in org.enrolled_clinics:
        if row.clinic is None:
            continue
        enrolled.append(
            EnrolledClinicRead(
                id=row.id,
                clinic_id=row.clinic_id,
                clinic_name=row.clinic.name,
                clinic_slug=row.clinic.slug,
                status=row.status,
                enrolled_at=row.enrolled_at,
            )
        )
    enrolled.sort(key=lambda e: e.clinic_name.lower())

    return OrganizationDetailRead(
        id=org.id,
        name=org.name,
        slug=org.slug,
        status=org.status,
        is_owner=org.owner_id == user.id,
        subscription=sub_read,
        enrolled_clinics=enrolled,
    )


async def list_enrollments(db: AsyncSession, org_id: uuid.UUID) -> list[EnrolledClinicRead]:
    result = await db.execute(
        select(OrganizationEnrolledClinic, Clinic)
        .join(Clinic, Clinic.id == OrganizationEnrolledClinic.clinic_id)
        .where(OrganizationEnrolledClinic.organization_id == org_id)
        .order_by(Clinic.name)
    )
    rows: list[EnrolledClinicRead] = []
    for enrollment, clinic in result.all():
        rows.append(
            EnrolledClinicRead(
                id=enrollment.id,
                clinic_id=enrollment.clinic_id,
                clinic_name=clinic.name,
                clinic_slug=clinic.slug,
                status=enrollment.status,
                enrolled_at=enrollment.enrolled_at,
            )
        )
    return rows


async def get_enrollment_for_clinic(
    db: AsyncSession, clinic_id: uuid.UUID
) -> OrganizationEnrolledClinic | None:
    result = await db.execute(
        select(OrganizationEnrolledClinic).where(OrganizationEnrolledClinic.clinic_id == clinic_id)
    )
    return result.scalar_one_or_none()


async def is_clinic_enrollment_active(db: AsyncSession, clinic_id: uuid.UUID) -> bool:
    enrollment = await get_enrollment_for_clinic(db, clinic_id)
    if enrollment is None:
        return True
    return enrollment.status == "active"


async def transfer_clinic_ownership(
    db: AsyncSession,
    clinic: Clinic,
    actor_membership: ClinicMembership,
    new_owner_membership_id: uuid.UUID,
) -> ClinicMembership:
    if actor_membership.role != "owner":
        raise HTTPException(status_code=403, detail="Owner only")
    if actor_membership.clinic_id != clinic.id:
        raise HTTPException(status_code=403, detail="Clinic scope mismatch")

    target = await db.get(ClinicMembership, new_owner_membership_id)
    if target is None or target.clinic_id != clinic.id or not target.is_active:
        raise HTTPException(status_code=404, detail="Membership not found")
    if target.id == actor_membership.id:
        raise HTTPException(status_code=400, detail="Already the owner")
    if target.role == "owner":
        raise HTTPException(status_code=400, detail="Target is already owner")

    actor_membership.role = "admin"
    target.role = "owner"

    db.add(
        ActivityLog(
            clinic_id=clinic.id,
            actor_user_id=actor_membership.user_id,
            actor_type="user",
            action="clinic.ownership_transferred",
            target_type="clinic_membership",
            target_id=str(target.id),
            summary="Clinic ownership transferred",
        )
    )
    await db.commit()
    await db.refresh(target)
    return target

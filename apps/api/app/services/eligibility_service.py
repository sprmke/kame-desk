import uuid
from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import paginate, parse_sort
from app.models import ActivityLog, ClinicMembership, EligibilityCheck, Patient, User
from app.schemas.payer_workflow import EligibilityCheckCreate, EligibilityCheckUpdate
from app.services.billing_access import assert_billing_read, assert_billing_write
from app.services.claims_partner import get_claims_partner
from app.services.patient_service import get_patient


async def list_eligibility_checks(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    membership: ClinicMembership,
    *,
    patient_id: uuid.UUID | None = None,
    status: str | None = None,
    payer_type: str | None = None,
    q: str | None = None,
    page: int | None = None,
    page_size: int | None = None,
    sort: str | None = None,
) -> tuple[list[EligibilityCheck], int]:
    assert_billing_read(membership)
    query = select(EligibilityCheck).where(EligibilityCheck.clinic_id == clinic_id)
    joined_patient = False
    sort_key = (sort or "checked_at").split(":", 1)[0]
    if patient_id:
        query = query.where(EligibilityCheck.patient_id == patient_id)
    if status:
        query = query.where(EligibilityCheck.status == status)
    if payer_type:
        query = query.where(EligibilityCheck.payer_type == payer_type)
    if (q and q.strip()) or sort_key == "patient":
        query = query.join(Patient, Patient.id == EligibilityCheck.patient_id)
        joined_patient = True
    if q and q.strip():
        term = f"%{q.strip()}%"
        query = query.where(
            Patient.full_name.ilike(term)
            | EligibilityCheck.payer_name.ilike(term)
            | EligibilityCheck.member_id.ilike(term)
        )
    allowed = {
        "checked_at": EligibilityCheck.checked_at,
        "status": EligibilityCheck.status,
        "payer": EligibilityCheck.payer_name,
        "patient": Patient.full_name if joined_patient else EligibilityCheck.checked_at,
    }
    query = query.order_by(parse_sort(sort, allowed, "checked_at", "desc"))
    if page_size is None:
        result = await db.execute(query)
        items = list(result.scalars().unique().all())
        return items, len(items)
    return await paginate(db, query, page or 1, page_size)


async def create_eligibility_check(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    data: EligibilityCheckCreate,
    actor: User,
    membership: ClinicMembership,
) -> EligibilityCheck:
    assert_billing_write(membership)
    await get_patient(db, clinic_id, data.patient_id)
    now = datetime.now(UTC)
    check = EligibilityCheck(
        clinic_id=clinic_id,
        patient_id=data.patient_id,
        payer_name=data.payer_name.strip(),
        payer_type=data.payer_type,
        member_id=data.member_id,
        status="pending",
        notes=data.notes,
        checked_by_user_id=actor.id,
        checked_at=now,
    )
    db.add(check)
    await db.flush()
    partner = get_claims_partner()
    await partner.submit_eligibility_check(payer_name=check.payer_name, member_id=check.member_id)
    db.add(
        ActivityLog(
            clinic_id=clinic_id,
            actor_user_id=actor.id,
            actor_type="user",
            action="eligibility_check.created",
            target_type="eligibility_check",
            target_id=str(check.id),
            summary=f"Eligibility check requested for {check.payer_name}",
        )
    )
    await db.commit()
    await db.refresh(check)
    return check


async def update_eligibility_check(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    check_id: uuid.UUID,
    data: EligibilityCheckUpdate,
    actor: User,
    membership: ClinicMembership,
) -> EligibilityCheck:
    assert_billing_write(membership)
    result = await db.execute(
        select(EligibilityCheck).where(
            EligibilityCheck.id == check_id, EligibilityCheck.clinic_id == clinic_id
        )
    )
    check = result.scalar_one_or_none()
    if check is None:
        raise HTTPException(status_code=404, detail="Eligibility check not found")
    payload = data.model_dump(exclude_unset=True)
    for key, value in payload.items():
        setattr(check, key, value)
    db.add(
        ActivityLog(
            clinic_id=clinic_id,
            actor_user_id=actor.id,
            actor_type="user",
            action="eligibility_check.updated",
            target_type="eligibility_check",
            target_id=str(check.id),
            summary=f"Eligibility check for {check.payer_name} marked {check.status}",
        )
    )
    await db.commit()
    await db.refresh(check)
    if payload.get("status") in ("failed", "ineligible"):
        from app.services.notification_service import notify_eligibility_updated

        await notify_eligibility_updated(
            db,
            clinic_id=clinic_id,
            check_id=check.id,
            status=check.status,
            actor_user_id=actor.id,
        )
    return check


async def eligibility_patient_names(
    db: AsyncSession, checks: list[EligibilityCheck]
) -> dict[uuid.UUID, str]:
    if not checks:
        return {}
    ids = {c.patient_id for c in checks}
    result = await db.execute(select(Patient).where(Patient.id.in_(ids)))
    return {p.id: p.full_name for p in result.scalars().all()}

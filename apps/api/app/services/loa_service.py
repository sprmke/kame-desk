import uuid
from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import paginate, parse_sort
from app.models import ActivityLog, ClinicMembership, InsuranceClaim, LoaRequest, Patient, User
from app.schemas.payer_workflow import LoaRequestCreate, LoaRequestUpdate
from app.services.billing_access import assert_billing_read, assert_billing_write
from app.services.claims_partner import get_claims_partner
from app.services.patient_service import get_patient

_TERMINAL_STATUSES = {"approved", "denied"}


async def list_loa_requests(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    membership: ClinicMembership,
    *,
    patient_id: uuid.UUID | None = None,
    status: str | None = None,
    q: str | None = None,
    page: int | None = None,
    page_size: int | None = None,
    sort: str | None = None,
) -> tuple[list[LoaRequest], int]:
    assert_billing_read(membership)
    query = select(LoaRequest).where(LoaRequest.clinic_id == clinic_id)
    joined_patient = False
    sort_key = (sort or "created_at").split(":", 1)[0]
    if patient_id:
        query = query.where(LoaRequest.patient_id == patient_id)
    if status:
        query = query.where(LoaRequest.status == status)
    if (q and q.strip()) or sort_key == "patient":
        query = query.join(Patient, Patient.id == LoaRequest.patient_id)
        joined_patient = True
    if q and q.strip():
        term = f"%{q.strip()}%"
        query = query.where(
            Patient.full_name.ilike(term)
            | LoaRequest.hmo_name.ilike(term)
            | LoaRequest.reference_number.ilike(term)
        )
    allowed = {
        "created_at": LoaRequest.created_at,
        "status": LoaRequest.status,
        "payer": LoaRequest.hmo_name,
        "patient": Patient.full_name if joined_patient else LoaRequest.created_at,
    }
    query = query.order_by(parse_sort(sort, allowed, "created_at", "desc"))
    if page_size is None:
        result = await db.execute(query)
        items = list(result.scalars().unique().all())
        return items, len(items)
    return await paginate(db, query, page or 1, page_size)


async def create_loa_request(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    data: LoaRequestCreate,
    actor: User,
    membership: ClinicMembership,
) -> LoaRequest:
    assert_billing_write(membership)
    await get_patient(db, clinic_id, data.patient_id)
    if data.claim_id:
        claim = await db.get(InsuranceClaim, data.claim_id)
        if claim is None or claim.clinic_id != clinic_id or claim.patient_id != data.patient_id:
            raise HTTPException(status_code=400, detail="Claim does not match patient")
    loa = LoaRequest(
        clinic_id=clinic_id,
        patient_id=data.patient_id,
        claim_id=data.claim_id,
        hmo_name=data.hmo_name.strip(),
        status="requested",
        requested_by_user_id=actor.id,
    )
    db.add(loa)
    await db.flush()
    db.add(
        ActivityLog(
            clinic_id=clinic_id,
            actor_user_id=actor.id,
            actor_type="user",
            action="loa_request.created",
            target_type="loa_request",
            target_id=str(loa.id),
            summary=f"LOA requested from {loa.hmo_name}",
        )
    )
    await db.commit()
    await db.refresh(loa)
    return loa


async def update_loa_request(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    loa_id: uuid.UUID,
    data: LoaRequestUpdate,
    actor: User,
    membership: ClinicMembership,
) -> LoaRequest:
    assert_billing_write(membership)
    result = await db.execute(
        select(LoaRequest).where(LoaRequest.id == loa_id, LoaRequest.clinic_id == clinic_id)
    )
    loa = result.scalar_one_or_none()
    if loa is None:
        raise HTTPException(status_code=404, detail="LOA request not found")

    payload = data.model_dump(exclude_unset=True)
    new_status = payload.get("status")
    if "claim_id" in payload and payload["claim_id"] is not None:
        claim = await db.get(InsuranceClaim, payload["claim_id"])
        if claim is None or claim.clinic_id != clinic_id or claim.patient_id != loa.patient_id:
            raise HTTPException(status_code=400, detail="Claim does not match patient")
    now = datetime.now(UTC)
    for key, value in payload.items():
        setattr(loa, key, value)

    if new_status == "submitted" and loa.submitted_at is None:
        loa.submitted_at = now
        partner = get_claims_partner()
        await partner.submit_loa_request(
            hmo_name=loa.hmo_name, reference_number=loa.reference_number
        )
    if new_status in _TERMINAL_STATUSES and loa.decided_at is None:
        loa.decided_at = now

    db.add(
        ActivityLog(
            clinic_id=clinic_id,
            actor_user_id=actor.id,
            actor_type="user",
            action="loa_request.status_changed",
            target_type="loa_request",
            target_id=str(loa.id),
            summary=f"LOA from {loa.hmo_name} now {loa.status}",
        )
    )
    await db.commit()
    await db.refresh(loa)
    if new_status:
        from app.services.notification_service import notify_loa_status

        await notify_loa_status(
            db,
            clinic_id=clinic_id,
            loa_id=loa.id,
            status=loa.status,
            actor_user_id=actor.id,
        )
    return loa


async def loa_patient_names(db: AsyncSession, requests: list[LoaRequest]) -> dict[uuid.UUID, str]:
    if not requests:
        return {}
    ids = {r.patient_id for r in requests}
    result = await db.execute(select(Patient).where(Patient.id.in_(ids)))
    return {p.id: p.full_name for p in result.scalars().all()}

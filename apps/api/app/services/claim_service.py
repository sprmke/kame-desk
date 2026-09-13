import uuid
from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import paginate, parse_sort
from app.models import ActivityLog, ClinicMembership, InsuranceClaim, Invoice, Patient, User
from app.schemas.claim import InsuranceClaimCreate, InsuranceClaimUpdate
from app.services.billing_access import assert_billing_write
from app.services.patient_service import get_patient


async def list_claims(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    *,
    status: str | None = None,
    patient_id: uuid.UUID | None = None,
    payer_type: str | None = None,
    q: str | None = None,
    page: int | None = None,
    page_size: int | None = None,
    sort: str | None = None,
) -> tuple[list[InsuranceClaim], int]:
    query = select(InsuranceClaim).where(InsuranceClaim.clinic_id == clinic_id)
    joined_patient = False
    sort_key = (sort or "created_at").split(":", 1)[0]
    if status:
        query = query.where(InsuranceClaim.status == status)
    if patient_id:
        query = query.where(InsuranceClaim.patient_id == patient_id)
    if payer_type:
        query = query.where(InsuranceClaim.payer_type == payer_type)
    if (q and q.strip()) or sort_key == "patient":
        query = query.join(Patient, Patient.id == InsuranceClaim.patient_id)
        joined_patient = True
    if q and q.strip():
        term = f"%{q.strip()}%"
        query = query.where(
            Patient.full_name.ilike(term)
            | InsuranceClaim.provider.ilike(term)
            | InsuranceClaim.claim_reference.ilike(term)
        )
    allowed = {
        "created_at": InsuranceClaim.created_at,
        "amount": InsuranceClaim.amount,
        "status": InsuranceClaim.status,
        "patient": Patient.full_name if joined_patient else InsuranceClaim.created_at,
    }
    query = query.order_by(parse_sort(sort, allowed, "created_at", "desc"))
    if page_size is None:
        result = await db.execute(query)
        items = list(result.scalars().unique().all())
        return items, len(items)
    return await paginate(db, query, page or 1, page_size)


async def create_claim(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    data: InsuranceClaimCreate,
    actor: User,
    membership: ClinicMembership,
) -> InsuranceClaim:
    assert_billing_write(membership)
    await get_patient(db, clinic_id, data.patient_id)
    if data.invoice_id:
        invoice = await db.get(Invoice, data.invoice_id)
        if (
            invoice is None
            or invoice.clinic_id != clinic_id
            or invoice.patient_id != data.patient_id
        ):
            raise HTTPException(status_code=400, detail="Invoice does not match patient")
    now = datetime.now(UTC)
    claim = InsuranceClaim(
        clinic_id=clinic_id,
        patient_id=data.patient_id,
        invoice_id=data.invoice_id,
        provider=data.provider.strip(),
        payer_type=data.payer_type,
        member_id=data.member_id,
        claim_reference=data.claim_reference,
        amount=data.amount,
        status="draft",
        notes=data.notes,
        loa_request_id=data.loa_request_id,
        created_by_user_id=actor.id,
    )
    claim.created_at = now
    claim.updated_at = now
    db.add(claim)
    await db.flush()
    db.add(
        ActivityLog(
            clinic_id=clinic_id,
            actor_user_id=actor.id,
            actor_type="user",
            action="insurance_claim.created",
            target_type="insurance_claim",
            target_id=str(claim.id),
            summary="HMO claim created",
        )
    )
    await db.commit()
    await db.refresh(claim)
    return claim


async def update_claim(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    claim_id: uuid.UUID,
    data: InsuranceClaimUpdate,
    actor: User,
    membership: ClinicMembership,
) -> InsuranceClaim:
    assert_billing_write(membership)
    result = await db.execute(
        select(InsuranceClaim).where(
            InsuranceClaim.id == claim_id, InsuranceClaim.clinic_id == clinic_id
        )
    )
    claim = result.scalar_one_or_none()
    if claim is None:
        raise HTTPException(status_code=404, detail="Claim not found")
    payload = data.model_dump(exclude_unset=True)
    for key, value in payload.items():
        setattr(claim, key, value)
    db.add(
        ActivityLog(
            clinic_id=clinic_id,
            actor_user_id=actor.id,
            actor_type="user",
            action="insurance_claim.updated",
            target_type="insurance_claim",
            target_id=str(claim.id),
            summary="HMO claim updated",
        )
    )
    await db.commit()
    await db.refresh(claim)
    if payload.get("status") == "denied":
        from app.services.notification_service import notify_claim_denied

        await notify_claim_denied(
            db,
            clinic_id=clinic_id,
            claim_id=claim.id,
            actor_user_id=actor.id,
        )
    return claim


async def claim_patient_names(
    db: AsyncSession, claims: list[InsuranceClaim]
) -> dict[uuid.UUID, str]:
    if not claims:
        return {}
    ids = {c.patient_id for c in claims}
    result = await db.execute(select(Patient).where(Patient.id.in_(ids)))
    return {p.id: p.full_name for p in result.scalars().all()}


async def claim_invoice_numbers(
    db: AsyncSession, claims: list[InsuranceClaim]
) -> dict[uuid.UUID, str]:
    invoice_ids = {c.invoice_id for c in claims if c.invoice_id}
    if not invoice_ids:
        return {}
    result = await db.execute(select(Invoice).where(Invoice.id.in_(invoice_ids)))
    return {i.id: i.invoice_number or "" for i in result.scalars().all()}

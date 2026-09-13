import uuid
from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    ActivityLog,
    ClinicMembership,
    Invoice,
    ToothChartEntry,
    User,
)
from app.schemas.billing import InvoiceCreate, InvoiceLineItemCreate
from app.schemas.tooth_chart import ToothChartAddToInvoiceRequest, ToothChartEntryCreate
from app.services import invoice_service
from app.services.patient_service import get_patient


async def list_entries(
    db: AsyncSession, clinic_id: uuid.UUID, patient_id: uuid.UUID
) -> list[ToothChartEntry]:
    await get_patient(db, clinic_id, patient_id)
    result = await db.execute(
        select(ToothChartEntry)
        .where(ToothChartEntry.clinic_id == clinic_id, ToothChartEntry.patient_id == patient_id)
        .order_by(ToothChartEntry.noted_at.desc())
    )
    return list(result.scalars().all())


async def create_entry(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    patient_id: uuid.UUID,
    data: ToothChartEntryCreate,
    actor: User,
) -> ToothChartEntry:
    await get_patient(db, clinic_id, patient_id)
    entry = ToothChartEntry(
        clinic_id=clinic_id,
        patient_id=patient_id,
        appointment_id=data.appointment_id,
        soap_note_id=data.soap_note_id,
        tooth_number=data.tooth_number,
        surface=data.surface,
        condition=data.condition,
        status=data.status,
        procedure_code=data.procedure_code,
        noted_at=datetime.now(UTC),
        created_by_user_id=actor.id,
        created_at=datetime.now(UTC),
    )
    db.add(entry)
    await db.flush()
    db.add(
        ActivityLog(
            clinic_id=clinic_id,
            actor_user_id=actor.id,
            actor_type="user",
            action="tooth_chart.updated",
            target_type="patient",
            target_id=str(patient_id),
            summary=f"Tooth {data.tooth_number} charted: {data.condition}",
        )
    )
    await db.commit()
    await db.refresh(entry)
    return entry


async def add_entry_to_invoice(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    patient_id: uuid.UUID,
    entry_id: uuid.UUID,
    data: ToothChartAddToInvoiceRequest,
    actor: User,
    membership: ClinicMembership,
) -> tuple[ToothChartEntry, Invoice]:
    await get_patient(db, clinic_id, patient_id)
    # Row-locked so two concurrent add-to-invoice calls for the same entry (a retried
    # request, a double-tap) can't both observe status="planned" and double-bill it.
    result = await db.execute(
        select(ToothChartEntry)
        .where(
            ToothChartEntry.id == entry_id,
            ToothChartEntry.clinic_id == clinic_id,
            ToothChartEntry.patient_id == patient_id,
        )
        .with_for_update()
    )
    entry = result.scalar_one_or_none()
    if entry is None:
        raise HTTPException(status_code=404, detail="Tooth chart entry not found")
    if entry.status != "planned":
        raise HTTPException(
            status_code=400, detail="Only planned entries can be added to an invoice"
        )

    appointment_id = data.appointment_id or entry.appointment_id
    # Only reuse an existing draft when we know which visit this belongs to — without an
    # appointment_id, "any draft for this patient" could silently attach the procedure to an
    # unrelated older draft invoice, so a fresh appointment_id-less entry always gets its own.
    draft = None
    if appointment_id:
        result = await db.execute(
            select(Invoice)
            .where(
                Invoice.patient_id == patient_id,
                Invoice.clinic_id == clinic_id,
                Invoice.status == "draft",
                Invoice.appointment_id == appointment_id,
            )
            .order_by(Invoice.created_at.desc())
        )
        draft = result.scalars().first()

    line_item_data = InvoiceLineItemCreate(
        description=data.description, category="procedure", unit_price=data.amount
    )
    if draft is None:
        invoice = await invoice_service.create_invoice(
            db,
            clinic_id,
            patient_id,
            InvoiceCreate(appointment_id=appointment_id, line_items=[line_item_data]),
            actor,
            membership,
        )
    else:
        invoice = await invoice_service.add_line_item(
            db, clinic_id, draft.id, line_item_data, actor, membership
        )

    # invoice.line_items is already loaded (both service calls refresh it before returning);
    # picking the max sort_order avoids a second, racy round-trip query for "the new item".
    new_item = max(invoice.line_items, key=lambda li: li.sort_order)

    entry.status = "completed"
    entry.invoice_line_item_id = new_item.id
    db.add(
        ActivityLog(
            clinic_id=clinic_id,
            actor_user_id=actor.id,
            actor_type="user",
            action="tooth_chart.updated",
            target_type="patient",
            target_id=str(patient_id),
            summary=f"Tooth {entry.tooth_number} procedure added to invoice",
        )
    )
    await db.commit()
    await db.refresh(entry)
    return entry, invoice

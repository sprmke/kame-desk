import uuid
from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.pagination import paginate, parse_sort
from app.models import (
    ActivityLog,
    Appointment,
    Clinic,
    ClinicMembership,
    CreditNote,
    DoctorProfile,
    Invoice,
    InvoiceLineItem,
    Patient,
    Payment,
    ToothChartEntry,
    User,
)
from app.schemas.billing import (
    CreditNoteCreate,
    InvoiceCreate,
    InvoiceLineItemCreate,
    InvoiceLineItemUpdate,
    PaymentCreate,
)
from app.services import invoice_pdf
from app.services.billing_access import (
    assert_billing_void,
    assert_billing_write,
    assert_invoice_read,
)
from app.services.clinical_access import get_doctor_profile_for_user
from app.services.membership_service import maybe_apply_membership_waiver
from app.services.patient_service import get_patient
from app.services.report_service import get_revenue_totals
from app.services.storage_service import upload_object_bytes

TWO_PLACES = Decimal("0.01")
DEFAULT_NUMBERING = {"prefix": "OR-", "next_number": 1, "pad_width": 6}


def money(value: Decimal) -> Decimal:
    return value.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def line_amount(quantity: Decimal, unit_price: Decimal) -> Decimal:
    return money(quantity * unit_price)


def _recalculate_totals(invoice: Invoice) -> None:
    subtotal = sum((item.amount for item in invoice.line_items), Decimal("0"))
    invoice.subtotal = money(subtotal)
    invoice.total = invoice.subtotal


def _amount_paid(invoice: Invoice) -> Decimal:
    return money(sum((p.amount for p in invoice.payments), Decimal("0")))


def _amount_credited(invoice: Invoice) -> Decimal:
    notes = getattr(invoice, "credit_notes", None) or []
    return money(sum((n.amount for n in notes), Decimal("0")))


def _sync_payment_status(invoice: Invoice) -> None:
    if invoice.status == "void":
        return
    if invoice.status == "draft":
        return
    paid = _amount_paid(invoice)
    if paid >= invoice.total:
        invoice.status = "paid"
    elif paid > Decimal("0"):
        invoice.status = "partially_paid"
    else:
        invoice.status = "issued"


async def _get_invoice(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    invoice_id: uuid.UUID,
) -> Invoice:
    result = await db.execute(
        select(Invoice)
        .options(
            selectinload(Invoice.line_items),
            selectinload(Invoice.payments),
            selectinload(Invoice.credit_notes),
        )
        .where(Invoice.id == invoice_id, Invoice.clinic_id == clinic_id)
    )
    invoice = result.scalar_one_or_none()
    if invoice is None:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice


async def _assert_draft(invoice: Invoice) -> None:
    if invoice.status != "draft":
        raise HTTPException(status_code=400, detail="Invoice is not editable")


async def _suggest_consultation_line(
    db: AsyncSession,
    appointment_id: uuid.UUID | None,
    clinic_id: uuid.UUID,
) -> InvoiceLineItemCreate | None:
    if appointment_id is None:
        return None
    result = await db.execute(
        select(Appointment, DoctorProfile)
        .join(DoctorProfile, DoctorProfile.id == Appointment.doctor_id)
        .where(Appointment.id == appointment_id, Appointment.clinic_id == clinic_id)
    )
    row = result.one_or_none()
    if row is None:
        return None
    _appt, doctor = row
    if doctor.consultation_fee is None:
        return None
    fee = money(Decimal(str(doctor.consultation_fee)))
    if fee <= Decimal("0"):
        return None
    return InvoiceLineItemCreate(
        description="Consultation",
        category="consultation",
        quantity=Decimal("1"),
        unit_price=fee,
    )


async def create_invoice(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    patient_id: uuid.UUID,
    data: InvoiceCreate,
    actor: User,
    membership: ClinicMembership,
) -> Invoice:
    assert_billing_write(membership)
    await get_patient(db, clinic_id, patient_id)

    if data.appointment_id is not None:
        appt = await db.get(Appointment, data.appointment_id)
        if appt is None or appt.clinic_id != clinic_id or appt.patient_id != patient_id:
            raise HTTPException(status_code=400, detail="Invalid appointment")

    invoice = Invoice(
        clinic_id=clinic_id,
        patient_id=patient_id,
        appointment_id=data.appointment_id,
        status="draft",
        created_by_user_id=actor.id,
    )
    db.add(invoice)
    await db.flush()

    line_items = list(data.line_items)
    if not line_items:
        suggested = await _suggest_consultation_line(db, data.appointment_id, clinic_id)
        if suggested:
            line_items = [suggested]

    for idx, item in enumerate(line_items):
        amount = line_amount(item.quantity, item.unit_price)
        db.add(
            InvoiceLineItem(
                invoice_id=invoice.id,
                description=item.description,
                category=item.category,
                quantity=item.quantity,
                unit_price=item.unit_price,
                amount=amount,
                hmo_covered_amount=item.hmo_covered_amount,
                hmo_claim_reference=item.hmo_claim_reference,
                sort_order=idx,
            )
        )

    await db.flush()
    await db.refresh(invoice, ["line_items"])

    for line_item in list(invoice.line_items):
        await maybe_apply_membership_waiver(db, invoice, line_item, clinic_id=clinic_id)
    await db.flush()
    await db.refresh(invoice, ["line_items"])
    _recalculate_totals(invoice)

    db.add(
        ActivityLog(
            clinic_id=clinic_id,
            actor_user_id=actor.id,
            actor_type="user",
            action="invoice.created",
            target_type="invoice",
            target_id=str(invoice.id),
            summary="Invoice draft created",
        )
    )
    await db.commit()
    return await _get_invoice(db, clinic_id, invoice.id)


async def list_patient_invoices(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    patient_id: uuid.UUID,
    membership: ClinicMembership,
    user: User,
) -> list[Invoice]:
    await get_patient(db, clinic_id, patient_id)
    query = (
        select(Invoice)
        .options(
            selectinload(Invoice.line_items),
            selectinload(Invoice.payments),
            selectinload(Invoice.credit_notes),
        )
        .where(Invoice.patient_id == patient_id, Invoice.clinic_id == clinic_id)
        .order_by(Invoice.created_at.desc())
    )

    if membership.role == "doctor":
        doctor = await get_doctor_profile_for_user(db, user, clinic_id)
        if doctor is None:
            return []
        query = query.join(
            Appointment,
            Appointment.id == Invoice.appointment_id,
        ).where(Appointment.doctor_id == doctor.id)

    result = await db.execute(query)
    return list(result.scalars().unique().all())


async def get_invoice(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    invoice_id: uuid.UUID,
) -> Invoice:
    return await _get_invoice(db, clinic_id, invoice_id)


async def add_line_item(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    invoice_id: uuid.UUID,
    data: InvoiceLineItemCreate,
    actor: User,
    membership: ClinicMembership,
    *,
    actor_type: str = "user",
) -> Invoice:
    assert_billing_write(membership)
    invoice = await _get_invoice(db, clinic_id, invoice_id)
    await _assert_draft(invoice)
    sort_order = max((i.sort_order for i in invoice.line_items), default=-1) + 1
    amount = line_amount(data.quantity, data.unit_price)
    new_item = InvoiceLineItem(
        invoice_id=invoice.id,
        description=data.description,
        category=data.category,
        quantity=data.quantity,
        unit_price=data.unit_price,
        amount=amount,
        hmo_covered_amount=data.hmo_covered_amount,
        hmo_claim_reference=data.hmo_claim_reference,
        sort_order=sort_order,
    )
    db.add(new_item)
    await db.flush()
    await db.refresh(invoice, ["line_items"])
    await maybe_apply_membership_waiver(db, invoice, new_item, clinic_id=clinic_id)
    await db.flush()
    await db.refresh(invoice, ["line_items"])
    _recalculate_totals(invoice)
    db.add(
        ActivityLog(
            clinic_id=clinic_id,
            actor_user_id=actor.id,
            actor_type=actor_type,
            action="invoice.updated",
            target_type="invoice",
            target_id=str(invoice.id),
            summary="Invoice line item added",
        )
    )
    await db.commit()
    return await _get_invoice(db, clinic_id, invoice.id)


async def update_line_item(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    invoice_id: uuid.UUID,
    item_id: uuid.UUID,
    data: InvoiceLineItemUpdate,
    actor: User,
    membership: ClinicMembership,
) -> Invoice:
    assert_billing_write(membership)
    invoice = await _get_invoice(db, clinic_id, invoice_id)
    await _assert_draft(invoice)
    item = next((i for i in invoice.line_items if i.id == item_id), None)
    if item is None:
        raise HTTPException(status_code=404, detail="Line item not found")
    updates = data.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(item, key, value)
    item.amount = line_amount(item.quantity, item.unit_price)
    _recalculate_totals(invoice)
    db.add(
        ActivityLog(
            clinic_id=clinic_id,
            actor_user_id=actor.id,
            actor_type="user",
            action="invoice.updated",
            target_type="invoice",
            target_id=str(invoice.id),
            summary="Invoice line item updated",
        )
    )
    await db.commit()
    return await _get_invoice(db, clinic_id, invoice.id)


async def delete_line_item(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    invoice_id: uuid.UUID,
    item_id: uuid.UUID,
    actor: User,
    membership: ClinicMembership,
) -> Invoice:
    assert_billing_write(membership)
    invoice = await _get_invoice(db, clinic_id, invoice_id)
    await _assert_draft(invoice)
    item = next((i for i in invoice.line_items if i.id == item_id), None)
    if item is None:
        raise HTTPException(status_code=404, detail="Line item not found")

    # A tooth-chart procedure billed via this line item goes back to "planned" so it
    # reappears on the treatment plan instead of being silently orphaned (completed
    # but pointing at nothing) once the line item it was billed under disappears.
    chart_result = await db.execute(
        select(ToothChartEntry).where(ToothChartEntry.invoice_line_item_id == item.id)
    )
    for chart_entry in chart_result.scalars().all():
        chart_entry.status = "planned"
        chart_entry.invoice_line_item_id = None

    await db.delete(item)
    await db.flush()
    await db.refresh(invoice, ["line_items"])
    _recalculate_totals(invoice)
    db.add(
        ActivityLog(
            clinic_id=clinic_id,
            actor_user_id=actor.id,
            actor_type="user",
            action="invoice.updated",
            target_type="invoice",
            target_id=str(invoice.id),
            summary="Invoice line item removed",
        )
    )
    await db.commit()
    return await _get_invoice(db, clinic_id, invoice.id)


def _allocate_invoice_number(config: dict) -> tuple[str, dict]:
    merged = {**DEFAULT_NUMBERING, **(config or {})}
    next_number = int(merged["next_number"])
    prefix = str(merged.get("prefix", "OR-"))
    pad_width = int(merged.get("pad_width", 6))
    invoice_number = f"{prefix}{str(next_number).zfill(pad_width)}"
    merged["next_number"] = next_number + 1
    return invoice_number, merged


async def issue_invoice(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    invoice_id: uuid.UUID,
    actor: User,
    membership: ClinicMembership,
) -> Invoice:
    assert_billing_write(membership)
    invoice = await _get_invoice(db, clinic_id, invoice_id)
    if invoice.status != "draft":
        raise HTTPException(status_code=400, detail="Only draft invoices can be issued")
    if not invoice.line_items:
        raise HTTPException(status_code=400, detail="Invoice has no line items")

    clinic_result = await db.execute(select(Clinic).where(Clinic.id == clinic_id).with_for_update())
    clinic = clinic_result.scalar_one()
    invoice_number, updated_config = _allocate_invoice_number(
        clinic.receipt_numbering_config or DEFAULT_NUMBERING
    )
    clinic.receipt_numbering_config = updated_config

    invoice.invoice_number = invoice_number
    invoice.status = "issued"
    invoice.issued_at = datetime.now(UTC)
    _recalculate_totals(invoice)

    patient = await get_patient(db, clinic_id, invoice.patient_id)
    pdf_bytes = invoice_pdf.render_invoice_pdf(clinic, patient, invoice)
    object_key = f"invoices/{clinic_id}/{invoice.id}.pdf"
    upload_object_bytes(object_key, pdf_bytes, "application/pdf")
    invoice.pdf_object_key = object_key

    db.add(
        ActivityLog(
            clinic_id=clinic_id,
            actor_user_id=actor.id,
            actor_type="user",
            action="invoice.issued",
            target_type="invoice",
            target_id=str(invoice.id),
            summary=f"Invoice issued ({invoice_number})",
        )
    )
    await db.commit()
    return await _get_invoice(db, clinic_id, invoice.id)


async def send_invoice_to_financing(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    invoice_id: uuid.UUID,
    actor: User,
    membership: ClinicMembership,
) -> Invoice:
    from app.core.config import settings
    from app.services.financing_partner import get_financing_partner

    assert_billing_write(membership)
    if not settings.financing_partner_enabled:
        raise HTTPException(status_code=404, detail="Financing is not available for this clinic")
    invoice = await _get_invoice(db, clinic_id, invoice_id)
    if invoice.status == "draft":
        raise HTTPException(status_code=400, detail="Issue the invoice before sending to financing")
    if invoice.financing_status == "requested":
        raise HTTPException(status_code=400, detail="Already sent to financing")

    patient = await get_patient(db, clinic_id, invoice.patient_id)
    reference = await get_financing_partner().create_financing_request(
        invoice_id=invoice.id, amount=invoice.total, patient_name=patient.full_name
    )
    invoice.financing_status = "requested"
    db.add(
        ActivityLog(
            clinic_id=clinic_id,
            actor_user_id=actor.id,
            actor_type="user",
            action="invoice.sent_to_financing",
            target_type="invoice",
            target_id=str(invoice.id),
            summary="Invoice sent to financing partner",
            metadata_={"partner_reference": reference},
        )
    )
    await db.commit()
    return await _get_invoice(db, clinic_id, invoice.id)


async def record_payment(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    invoice_id: uuid.UUID,
    data: PaymentCreate,
    actor: User,
    membership: ClinicMembership,
) -> Invoice:
    assert_billing_write(membership)
    invoice = await _get_invoice(db, clinic_id, invoice_id)
    if invoice.status in ("draft", "void"):
        raise HTTPException(status_code=400, detail="Cannot record payment on this invoice")

    paid_at = data.paid_at or datetime.now(UTC)
    now = datetime.now(UTC)
    payment = Payment(
        invoice_id=invoice.id,
        clinic_id=clinic_id,
        method=data.method,
        amount=money(data.amount),
        paid_at=paid_at,
        reference_number=data.reference_number,
        recorded_by_user_id=actor.id,
        created_at=now,
    )
    db.add(payment)
    await db.flush()
    await db.refresh(invoice, ["payments"])
    _sync_payment_status(invoice)

    db.add(
        ActivityLog(
            clinic_id=clinic_id,
            actor_user_id=actor.id,
            actor_type="user",
            action="invoice.payment_recorded",
            target_type="invoice",
            target_id=str(invoice.id),
            summary="Payment recorded",
            metadata_={"amount": str(payment.amount), "method": payment.method},
        )
    )
    await db.commit()
    from app.services.notification_service import notify_invoice_payment

    inv = await _get_invoice(db, clinic_id, invoice.id)
    await notify_invoice_payment(
        db,
        clinic_id=clinic_id,
        invoice_id=inv.id,
        patient_id=inv.patient_id,
        actor_user_id=actor.id,
    )
    return inv


async def void_invoice(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    invoice_id: uuid.UUID,
    reason: str,
    actor: User,
    membership: ClinicMembership,
) -> Invoice:
    assert_billing_void(membership)
    invoice = await _get_invoice(db, clinic_id, invoice_id)
    if invoice.status == "void":
        raise HTTPException(status_code=400, detail="Invoice already void")
    if invoice.payments:
        raise HTTPException(
            status_code=400,
            detail="Cannot void invoice with recorded payments",
        )
    invoice.status = "void"
    invoice.void_reason = reason
    invoice.voided_at = datetime.now(UTC)
    db.add(
        ActivityLog(
            clinic_id=clinic_id,
            actor_user_id=actor.id,
            actor_type="user",
            action="invoice.voided",
            target_type="invoice",
            target_id=str(invoice.id),
            summary="Invoice voided",
        )
    )
    await db.commit()
    from app.services.notification_service import notify_invoice_voided_or_credit

    await notify_invoice_voided_or_credit(
        db,
        clinic_id=clinic_id,
        invoice_id=invoice_id,
        notif_type="invoice.voided",
        title="Invoice voided",
        actor_user_id=actor.id,
    )
    return await _get_invoice(db, clinic_id, invoice.id)


async def get_patient_balance(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    patient_id: uuid.UUID,
) -> tuple[Decimal, int]:
    """Outstanding balance across issued/partially_paid invoices."""
    await get_patient(db, clinic_id, patient_id)
    result = await db.execute(
        select(Invoice)
        .options(selectinload(Invoice.payments))
        .where(
            Invoice.clinic_id == clinic_id,
            Invoice.patient_id == patient_id,
            Invoice.status.in_(("issued", "partially_paid")),
        )
    )
    invoices = list(result.scalars().all())
    balance = Decimal("0")
    for inv in invoices:
        balance += inv.total - _amount_paid(inv)
    return money(balance), len(invoices)


async def get_outstanding_balances(
    db: AsyncSession,
    clinic_id: uuid.UUID,
) -> list[tuple[Patient, Decimal, datetime | None]]:
    result = await db.execute(
        select(Invoice, Patient)
        .join(Patient, Patient.id == Invoice.patient_id)
        .options(selectinload(Invoice.payments))
        .where(
            Invoice.clinic_id == clinic_id,
            Invoice.status.in_(("issued", "partially_paid")),
        )
    )
    by_patient: dict[uuid.UUID, dict] = {}
    for invoice, patient in result.all():
        due = invoice.total - _amount_paid(invoice)
        if due <= Decimal("0"):
            continue
        bucket = by_patient.setdefault(
            patient.id,
            {"patient": patient, "balance": Decimal("0"), "oldest": None},
        )
        bucket["balance"] += due
        issued = invoice.issued_at or invoice.created_at
        if bucket["oldest"] is None or issued < bucket["oldest"]:
            bucket["oldest"] = issued

    rows = [
        (b["patient"], money(b["balance"]), b["oldest"])
        for b in by_patient.values()
        if b["balance"] > Decimal("0")
    ]
    rows.sort(key=lambda r: r[1], reverse=True)
    return rows


async def get_revenue_summary(db: AsyncSession, clinic_id: uuid.UUID) -> dict[str, Decimal]:
    totals = await get_revenue_totals(db, clinic_id)
    return {k: money(Decimal(v)) for k, v in totals.items()}


async def get_invoice_for_read(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    invoice_id: uuid.UUID,
    membership: ClinicMembership,
    user: User,
) -> Invoice:
    invoice = await _get_invoice(db, clinic_id, invoice_id)
    await assert_invoice_read(db, membership, invoice, user)
    return invoice


async def get_invoice_pdf_bytes(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    invoice_id: uuid.UUID,
    membership: ClinicMembership,
    user: User,
) -> tuple[bytes, Invoice]:
    invoice = await get_invoice_for_read(db, clinic_id, invoice_id, membership, user)
    clinic = await db.get(Clinic, clinic_id)
    patient = await get_patient(db, clinic_id, invoice.patient_id)
    if clinic is None:
        raise HTTPException(status_code=404, detail="Clinic not found")
    return invoice_pdf.render_invoice_pdf(clinic, patient, invoice), invoice


def _allocate_credit_number(config: dict) -> tuple[str, dict]:
    merged = {**DEFAULT_NUMBERING, **(config or {})}
    next_number = int(merged.get("credit_next_number", 1))
    pad_width = int(merged.get("pad_width", 6))
    credit_number = f"CN-{str(next_number).zfill(pad_width)}"
    merged["credit_next_number"] = next_number + 1
    return credit_number, merged


async def list_clinic_invoices(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    membership: ClinicMembership,
    user: User,
    *,
    q: str | None = None,
    status: str | None = None,
    start_from: datetime | None = None,
    start_to: datetime | None = None,
    page: int | None = None,
    page_size: int | None = None,
    sort: str | None = None,
) -> tuple[list[Invoice], int]:
    query = (
        select(Invoice)
        .options(
            selectinload(Invoice.line_items),
            selectinload(Invoice.payments),
            selectinload(Invoice.credit_notes),
        )
        .where(Invoice.clinic_id == clinic_id)
    )
    if status:
        query = query.where(Invoice.status == status)
    if start_from:
        query = query.where(Invoice.created_at >= start_from)
    if start_to:
        query = query.where(Invoice.created_at <= start_to)
    if q:
        term = f"%{q.strip()}%"
        query = query.join(Patient, Patient.id == Invoice.patient_id).where(
            Patient.full_name.ilike(term) | Invoice.invoice_number.ilike(term)
        )
    if membership.role == "doctor":
        doctor = await get_doctor_profile_for_user(db, user, clinic_id)
        if doctor is None:
            return [], 0
        query = query.join(Appointment, Appointment.id == Invoice.appointment_id).where(
            Appointment.doctor_id == doctor.id
        )
    query = query.order_by(
        parse_sort(
            sort,
            {
                "created_at": Invoice.created_at,
                "total": Invoice.total,
                "status": Invoice.status,
            },
            "created_at",
            "desc",
        )
    )
    if page_size is None:
        result = await db.execute(query)
        items = list(result.scalars().unique().all())
        return items, len(items)
    return await paginate(db, query, page or 1, page_size)


async def create_credit_note(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    invoice_id: uuid.UUID,
    data: CreditNoteCreate,
    actor: User,
    membership: ClinicMembership,
) -> Invoice:
    assert_billing_void(membership)
    invoice = await _get_invoice(db, clinic_id, invoice_id)
    if invoice.status in ("draft", "void"):
        raise HTTPException(status_code=400, detail="Credit notes apply to issued invoices only")
    paid = _amount_paid(invoice)
    if paid <= Decimal("0"):
        raise HTTPException(status_code=400, detail="No payment to credit")
    already = _amount_credited(invoice)
    amount = money(data.amount)
    if already + amount > paid:
        raise HTTPException(status_code=400, detail="Credit exceeds amount paid")

    clinic_result = await db.execute(select(Clinic).where(Clinic.id == clinic_id).with_for_update())
    clinic = clinic_result.scalar_one()
    credit_number, updated_config = _allocate_credit_number(
        clinic.receipt_numbering_config or DEFAULT_NUMBERING
    )
    clinic.receipt_numbering_config = updated_config

    note = CreditNote(
        clinic_id=clinic_id,
        invoice_id=invoice.id,
        patient_id=invoice.patient_id,
        credit_number=credit_number,
        kind=data.kind,
        amount=amount,
        reason=data.reason.strip(),
        created_by_user_id=actor.id,
        created_at=datetime.now(UTC),
    )
    db.add(note)
    invoice.credit_notes.append(note)
    db.add(
        ActivityLog(
            clinic_id=clinic_id,
            actor_user_id=actor.id,
            actor_type="user",
            action="invoice.credit_issued",
            target_type="invoice",
            target_id=str(invoice.id),
            summary="Credit note issued",
            metadata_={"amount": str(amount), "kind": data.kind, "credit_number": credit_number},
        )
    )
    await db.commit()
    await db.refresh(invoice, ["credit_notes", "payments", "line_items"])
    from app.services.notification_service import notify_invoice_voided_or_credit

    await notify_invoice_voided_or_credit(
        db,
        clinic_id=clinic_id,
        invoice_id=invoice.id,
        notif_type="invoice.credit_issued",
        title="Credit issued",
        actor_user_id=actor.id,
    )
    return invoice

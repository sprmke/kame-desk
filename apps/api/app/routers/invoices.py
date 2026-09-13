import uuid
from datetime import datetime
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_db
from app.core.deps import ClinicStaff
from app.core.security import get_active_clinic_membership, get_current_user
from app.models import ClinicMembership, Invoice, Patient, User
from app.schemas.billing import (
    CreditNoteCreate,
    InvoiceCreate,
    InvoiceLineItemCreate,
    InvoiceLineItemUpdate,
    InvoiceListResponse,
    InvoiceRead,
    InvoiceVoid,
    OutstandingBalanceEntry,
    OutstandingBalancesResponse,
    PatientBalanceRead,
    PaymentCreate,
    RevenueSummaryRead,
)
from app.services.billing_access import assert_billing_read
from app.services.invoice_service import (
    _amount_credited,
    _amount_paid,
    add_line_item,
    create_credit_note,
    create_invoice,
    delete_line_item,
    get_invoice_for_read,
    get_invoice_pdf_bytes,
    get_outstanding_balances,
    get_patient_balance,
    get_revenue_summary,
    issue_invoice,
    list_clinic_invoices,
    list_patient_invoices,
    money,
    record_payment,
    send_invoice_to_financing,
    update_line_item,
    void_invoice,
)

router = APIRouter(tags=["billing"])


async def _clinic_id(
    membership: Annotated[ClinicMembership, Depends(get_active_clinic_membership)],
) -> uuid.UUID:
    return membership.clinic_id


def _to_read(invoice: Invoice, patient_name: str | None = None) -> InvoiceRead:
    paid = _amount_paid(invoice)
    credited = _amount_credited(invoice)
    row = InvoiceRead.model_validate(invoice)
    row.amount_paid = paid
    row.amount_credited = credited
    row.balance_due = money(max(invoice.total - paid, Decimal("0")))
    row.patient_name = patient_name
    row.financing_available = settings.financing_partner_enabled and invoice.status != "draft"
    return row


async def _enrich(
    db: AsyncSession,
    invoices: list[Invoice],
    patient_name: str | None = None,
) -> list[InvoiceRead]:
    if not invoices:
        return []
    if patient_name is None:
        patient_ids = {i.patient_id for i in invoices}
        result = await db.execute(select(Patient).where(Patient.id.in_(patient_ids)))
        name_map = {p.id: p.full_name for p in result.scalars().all()}
    else:
        name_map = {}
    return [_to_read(inv, patient_name or name_map.get(inv.patient_id)) for inv in invoices]


async def _filtered_invoices(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    membership: ClinicMembership,
    user: User,
    q: str | None,
    status: str | None,
    start_from: datetime | None,
    start_to: datetime | None,
    *,
    page: int | None = None,
    page_size: int | None = None,
    sort: str | None = None,
) -> tuple[list[InvoiceRead], int]:
    items, total = await list_clinic_invoices(
        db,
        clinic_id,
        membership,
        user,
        q=q,
        status=status,
        start_from=start_from,
        start_to=start_to,
        page=page,
        page_size=page_size,
        sort=sort,
    )
    return await _enrich(db, items), total


@router.get("/invoices/export")
async def export_invoices(
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    membership: ClinicStaff,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    q: str | None = None,
    status: str | None = None,
    start_from: datetime | None = None,
    start_to: datetime | None = None,
) -> Response:
    assert_billing_read(membership)
    enriched, _total = await _filtered_invoices(
        db, clinic_id, membership, user, q, status, start_from, start_to
    )
    lines = ["invoice_number,patient,status,total,paid,credited,balance"]
    for row in enriched:
        lines.append(
            ",".join(
                [
                    row.invoice_number or "",
                    (row.patient_name or "").replace(",", " "),
                    row.status,
                    str(row.total),
                    str(row.amount_paid),
                    str(row.amount_credited),
                    str(row.balance_due),
                ]
            )
        )
    return Response(
        content="\n".join(lines) + "\n",
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="invoices.csv"'},
    )


@router.get("/invoices", response_model=InvoiceListResponse)
async def list_invoices(
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    membership: ClinicStaff,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    q: str | None = None,
    status: str | None = None,
    start_from: datetime | None = None,
    start_to: datetime | None = None,
    page: int = Query(1, ge=1),
    page_size: int | None = Query(None, ge=1, le=100),
    sort: str | None = None,
) -> InvoiceListResponse:
    assert_billing_read(membership)
    enriched, total = await _filtered_invoices(
        db,
        clinic_id,
        membership,
        user,
        q,
        status,
        start_from,
        start_to,
        page=page,
        page_size=page_size,
        sort=sort,
    )
    return InvoiceListResponse(
        items=enriched,
        total=total,
        page=page,
        page_size=page_size or total or len(enriched),
    )


@router.post("/invoices/{invoice_id}/credit-notes", response_model=InvoiceRead)
async def post_credit_note(
    invoice_id: uuid.UUID,
    data: CreditNoteCreate,
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    membership: ClinicStaff,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> InvoiceRead:
    invoice = await create_credit_note(db, clinic_id, invoice_id, data, user, membership)
    enriched = await _enrich(db, [invoice])
    return enriched[0]


@router.post("/patients/{patient_id}/invoices", response_model=InvoiceRead)
async def post_invoice(
    patient_id: uuid.UUID,
    data: InvoiceCreate,
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    membership: ClinicStaff,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> InvoiceRead:
    invoice = await create_invoice(db, clinic_id, patient_id, data, user, membership)
    enriched = await _enrich(db, [invoice])
    return enriched[0]


@router.get("/patients/{patient_id}/invoices", response_model=InvoiceListResponse)
async def get_invoices(
    patient_id: uuid.UUID,
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    membership: ClinicStaff,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> InvoiceListResponse:
    assert_billing_read(membership)
    items = await list_patient_invoices(db, clinic_id, patient_id, membership, user)
    enriched = await _enrich(db, items)
    return InvoiceListResponse(items=enriched, total=len(enriched))


@router.get("/patients/{patient_id}/balance", response_model=PatientBalanceRead)
async def get_balance(
    patient_id: uuid.UUID,
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    membership: ClinicStaff,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PatientBalanceRead:
    assert_billing_read(membership)
    balance, count = await get_patient_balance(db, clinic_id, patient_id)
    return PatientBalanceRead(
        patient_id=patient_id,
        outstanding_balance=balance,
        invoice_count=count,
    )


@router.get("/invoices/{invoice_id}", response_model=InvoiceRead)
async def get_invoice(
    invoice_id: uuid.UUID,
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    membership: ClinicStaff,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> InvoiceRead:
    invoice = await get_invoice_for_read(db, clinic_id, invoice_id, membership, user)
    enriched = await _enrich(db, [invoice])
    return enriched[0]


@router.post("/invoices/{invoice_id}/line-items", response_model=InvoiceRead)
async def post_line_item(
    invoice_id: uuid.UUID,
    data: InvoiceLineItemCreate,
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    membership: ClinicStaff,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> InvoiceRead:
    invoice = await add_line_item(db, clinic_id, invoice_id, data, user, membership)
    enriched = await _enrich(db, [invoice])
    return enriched[0]


@router.patch(
    "/invoices/{invoice_id}/line-items/{item_id}",
    response_model=InvoiceRead,
)
async def patch_line_item(
    invoice_id: uuid.UUID,
    item_id: uuid.UUID,
    data: InvoiceLineItemUpdate,
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    membership: ClinicStaff,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> InvoiceRead:
    invoice = await update_line_item(db, clinic_id, invoice_id, item_id, data, user, membership)
    enriched = await _enrich(db, [invoice])
    return enriched[0]


@router.delete("/invoices/{invoice_id}/line-items/{item_id}", response_model=InvoiceRead)
async def delete_line_item_route(
    invoice_id: uuid.UUID,
    item_id: uuid.UUID,
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    membership: ClinicStaff,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> InvoiceRead:
    invoice = await delete_line_item(db, clinic_id, invoice_id, item_id, user, membership)
    enriched = await _enrich(db, [invoice])
    return enriched[0]


@router.post("/invoices/{invoice_id}/issue", response_model=InvoiceRead)
async def post_issue(
    invoice_id: uuid.UUID,
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    membership: ClinicStaff,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> InvoiceRead:
    invoice = await issue_invoice(db, clinic_id, invoice_id, user, membership)
    enriched = await _enrich(db, [invoice])
    return enriched[0]


@router.post("/invoices/{invoice_id}/send-to-financing", response_model=InvoiceRead)
async def post_send_to_financing(
    invoice_id: uuid.UUID,
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    membership: ClinicStaff,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> InvoiceRead:
    invoice = await send_invoice_to_financing(db, clinic_id, invoice_id, user, membership)
    enriched = await _enrich(db, [invoice])
    return enriched[0]


@router.post("/invoices/{invoice_id}/payments", response_model=InvoiceRead)
async def post_payment(
    invoice_id: uuid.UUID,
    data: PaymentCreate,
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    membership: ClinicStaff,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> InvoiceRead:
    invoice = await record_payment(db, clinic_id, invoice_id, data, user, membership)
    enriched = await _enrich(db, [invoice])
    return enriched[0]


@router.post("/invoices/{invoice_id}/void", response_model=InvoiceRead)
async def post_void(
    invoice_id: uuid.UUID,
    data: InvoiceVoid,
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    membership: ClinicStaff,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> InvoiceRead:
    invoice = await void_invoice(db, clinic_id, invoice_id, data.reason, user, membership)
    enriched = await _enrich(db, [invoice])
    return enriched[0]


@router.get("/invoices/{invoice_id}/receipt-pdf")
async def get_receipt_pdf(
    invoice_id: uuid.UUID,
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    membership: ClinicStaff,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    pdf_bytes, invoice = await get_invoice_pdf_bytes(db, clinic_id, invoice_id, membership, user)
    filename = invoice.invoice_number or str(invoice_id)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="receipt-{filename}.pdf"'},
    )


@router.get(
    "/clinics/{clinic_id}/outstanding-balances",
    response_model=OutstandingBalancesResponse,
)
async def get_outstanding(
    clinic_id: uuid.UUID,
    membership: Annotated[ClinicMembership, Depends(get_active_clinic_membership)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> OutstandingBalancesResponse:
    if membership.clinic_id != clinic_id:
        raise HTTPException(status_code=403, detail="Clinic mismatch")
    assert_billing_read(membership)
    rows = await get_outstanding_balances(db, clinic_id)
    items = [
        OutstandingBalanceEntry(
            patient_id=p.id,
            patient_name=p.full_name,
            outstanding_balance=bal,
            oldest_invoice_date=oldest,
        )
        for p, bal, oldest in rows
    ]
    total = money(sum((i.outstanding_balance for i in items), Decimal("0")))
    return OutstandingBalancesResponse(items=items, total_outstanding=total)


@router.get("/clinics/{clinic_id}/revenue-summary", response_model=RevenueSummaryRead)
async def get_revenue(
    clinic_id: uuid.UUID,
    membership: Annotated[ClinicMembership, Depends(get_active_clinic_membership)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RevenueSummaryRead:
    if membership.clinic_id != clinic_id:
        raise HTTPException(status_code=403, detail="Clinic mismatch")
    assert_billing_read(membership)
    summary = await get_revenue_summary(db, clinic_id)
    return RevenueSummaryRead(**summary)

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import ClinicStaff
from app.core.security import get_current_user
from app.models import User
from app.schemas.tooth_chart import (
    ToothChartAddToInvoiceRequest,
    ToothChartAddToInvoiceResponse,
    ToothChartEntryCreate,
    ToothChartEntryRead,
)
from app.services import tooth_chart_service
from app.services.clinic_service import get_clinic
from app.services.clinical_access import assert_clinical_notes_write, assert_soap_read

router = APIRouter(prefix="/patients/{patient_id}/tooth-chart", tags=["tooth-chart"])


@router.get("", response_model=list[ToothChartEntryRead])
async def get_tooth_chart(
    patient_id: uuid.UUID,
    membership: ClinicStaff,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[ToothChartEntryRead]:
    clinic = await get_clinic(db, membership.clinic_id)
    await assert_soap_read(db, membership, clinic)
    entries = await tooth_chart_service.list_entries(db, membership.clinic_id, patient_id)
    return [ToothChartEntryRead.model_validate(e) for e in entries]


@router.post("", response_model=ToothChartEntryRead)
async def post_tooth_chart_entry(
    patient_id: uuid.UUID,
    data: ToothChartEntryCreate,
    membership: ClinicStaff,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ToothChartEntryRead:
    await assert_clinical_notes_write(membership)
    entry = await tooth_chart_service.create_entry(db, membership.clinic_id, patient_id, data, user)
    return ToothChartEntryRead.model_validate(entry)


@router.post("/{entry_id}/add-to-invoice", response_model=ToothChartAddToInvoiceResponse)
async def post_add_to_invoice(
    patient_id: uuid.UUID,
    entry_id: uuid.UUID,
    data: ToothChartAddToInvoiceRequest,
    membership: ClinicStaff,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ToothChartAddToInvoiceResponse:
    await assert_clinical_notes_write(membership)
    entry, invoice = await tooth_chart_service.add_entry_to_invoice(
        db, membership.clinic_id, patient_id, entry_id, data, user, membership
    )
    return ToothChartAddToInvoiceResponse(
        entry=ToothChartEntryRead.model_validate(entry), invoice_id=invoice.id
    )

import base64
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import ClinicStaff
from app.core.security import get_active_clinic_membership, get_current_user
from app.models import ClinicMembership, User
from app.schemas.billing_assist import (
    BillingExtractionConfirm,
    BillingExtractionRequest,
    BillingExtractionResponse,
)
from app.services.billing_assist_service import extract_billing_document, mark_extraction_confirmed

router = APIRouter(tags=["billing-assist"])


async def _clinic_id(
    membership: Annotated[ClinicMembership, Depends(get_active_clinic_membership)],
) -> uuid.UUID:
    return membership.clinic_id


@router.post(
    "/patients/{patient_id}/billing-assist/extract",
    response_model=BillingExtractionResponse,
)
async def post_billing_extract(
    patient_id: uuid.UUID,
    data: BillingExtractionRequest,
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    membership: ClinicStaff,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> BillingExtractionResponse:
    raw = base64.b64decode(data.content_base64, validate=True)
    result = await extract_billing_document(
        db,
        clinic_id,
        patient_id,
        raw,
        data.content_type,
        data.filename,
        user,
        membership,
    )
    return BillingExtractionResponse.model_validate(result)


@router.post("/patients/{patient_id}/billing-assist/confirm-attempt")
async def post_billing_extract_confirm(
    patient_id: uuid.UUID,
    data: BillingExtractionConfirm,
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    membership: ClinicStaff,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, str]:
    await mark_extraction_confirmed(
        db, clinic_id, patient_id, uuid.UUID(data.attempt_id), user, membership
    )
    return {"status": "confirmed", "patient_id": str(patient_id)}

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import ClinicStaff
from app.core.security import get_active_clinic_membership, get_current_user
from app.models import ClinicMembership, User
from app.schemas.claim import (
    InsuranceClaimCreate,
    InsuranceClaimListResponse,
    InsuranceClaimRead,
    InsuranceClaimUpdate,
)
from app.services import claim_service
from app.services.billing_access import assert_billing_read

router = APIRouter(prefix="/claims", tags=["claims"])


async def _clinic_id(
    membership: Annotated[ClinicMembership, Depends(get_active_clinic_membership)],
) -> uuid.UUID:
    return membership.clinic_id


def _to_read(
    claim,
    names: dict[uuid.UUID, str],
    numbers: dict[uuid.UUID, str],
) -> InsuranceClaimRead:
    row = InsuranceClaimRead.model_validate(claim)
    row.patient_name = names.get(claim.patient_id)
    if claim.invoice_id:
        row.invoice_number = numbers.get(claim.invoice_id) or None
    return row


@router.get("", response_model=InsuranceClaimListResponse)
async def list_claims(
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    membership: ClinicStaff,
    db: Annotated[AsyncSession, Depends(get_db)],
    status: str | None = None,
    patient_id: uuid.UUID | None = None,
    payer_type: str | None = None,
    q: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int | None = Query(None, ge=1, le=100),
    sort: str | None = None,
) -> InsuranceClaimListResponse:
    assert_billing_read(membership)
    rows, total = await claim_service.list_claims(
        db,
        clinic_id,
        status=status,
        patient_id=patient_id,
        payer_type=payer_type,
        q=q,
        page=page,
        page_size=page_size,
        sort=sort,
    )
    names = await claim_service.claim_patient_names(db, rows)
    numbers = await claim_service.claim_invoice_numbers(db, rows)
    items = [_to_read(r, names, numbers) for r in rows]
    return InsuranceClaimListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size or total or len(items),
    )


@router.post("", response_model=InsuranceClaimRead)
async def create_claim(
    data: InsuranceClaimCreate,
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    membership: ClinicStaff,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> InsuranceClaimRead:
    claim = await claim_service.create_claim(db, clinic_id, data, user, membership)
    names = await claim_service.claim_patient_names(db, [claim])
    numbers = await claim_service.claim_invoice_numbers(db, [claim])
    return _to_read(claim, names, numbers)


@router.patch("/{claim_id}", response_model=InsuranceClaimRead)
async def patch_claim(
    claim_id: uuid.UUID,
    data: InsuranceClaimUpdate,
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    membership: ClinicStaff,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> InsuranceClaimRead:
    claim = await claim_service.update_claim(db, clinic_id, claim_id, data, user, membership)
    names = await claim_service.claim_patient_names(db, [claim])
    numbers = await claim_service.claim_invoice_numbers(db, [claim])
    return _to_read(claim, names, numbers)

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import ClinicStaff
from app.core.security import get_active_clinic_membership, get_current_user
from app.models import ClinicMembership, User
from app.schemas.payer_workflow import (
    EligibilityCheckCreate,
    EligibilityCheckListResponse,
    EligibilityCheckRead,
    EligibilityCheckUpdate,
)
from app.services import eligibility_service

router = APIRouter(prefix="/eligibility-checks", tags=["eligibility-checks"])


async def _clinic_id(
    membership: Annotated[ClinicMembership, Depends(get_active_clinic_membership)],
) -> uuid.UUID:
    return membership.clinic_id


def _to_read(check, names: dict[uuid.UUID, str]) -> EligibilityCheckRead:
    row = EligibilityCheckRead.model_validate(check)
    row.patient_name = names.get(check.patient_id)
    return row


@router.get("", response_model=EligibilityCheckListResponse)
async def list_eligibility_checks(
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    membership: ClinicStaff,
    db: Annotated[AsyncSession, Depends(get_db)],
    patient_id: uuid.UUID | None = None,
    status: str | None = None,
    payer_type: str | None = None,
    q: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int | None = Query(None, ge=1, le=100),
    sort: str | None = None,
) -> EligibilityCheckListResponse:
    rows, total = await eligibility_service.list_eligibility_checks(
        db,
        clinic_id,
        membership,
        patient_id=patient_id,
        status=status,
        payer_type=payer_type,
        q=q,
        page=page,
        page_size=page_size,
        sort=sort,
    )
    names = await eligibility_service.eligibility_patient_names(db, rows)
    items = [_to_read(r, names) for r in rows]
    return EligibilityCheckListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size or total or len(items),
    )


@router.post("", response_model=EligibilityCheckRead)
async def create_eligibility_check(
    data: EligibilityCheckCreate,
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    membership: ClinicStaff,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> EligibilityCheckRead:
    check = await eligibility_service.create_eligibility_check(
        db, clinic_id, data, user, membership
    )
    names = await eligibility_service.eligibility_patient_names(db, [check])
    return _to_read(check, names)


@router.patch("/{check_id}", response_model=EligibilityCheckRead)
async def patch_eligibility_check(
    check_id: uuid.UUID,
    data: EligibilityCheckUpdate,
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    membership: ClinicStaff,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> EligibilityCheckRead:
    check = await eligibility_service.update_eligibility_check(
        db, clinic_id, check_id, data, user, membership
    )
    names = await eligibility_service.eligibility_patient_names(db, [check])
    return _to_read(check, names)

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import ClinicStaff
from app.core.security import get_active_clinic_membership, get_current_user
from app.models import ClinicMembership, User
from app.schemas.payer_workflow import (
    LoaRequestCreate,
    LoaRequestListResponse,
    LoaRequestRead,
    LoaRequestUpdate,
)
from app.services import loa_service

router = APIRouter(prefix="/loa-requests", tags=["loa-requests"])


async def _clinic_id(
    membership: Annotated[ClinicMembership, Depends(get_active_clinic_membership)],
) -> uuid.UUID:
    return membership.clinic_id


def _to_read(loa, names: dict[uuid.UUID, str]) -> LoaRequestRead:
    row = LoaRequestRead.model_validate(loa)
    row.patient_name = names.get(loa.patient_id)
    return row


@router.get("", response_model=LoaRequestListResponse)
async def list_loa_requests(
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    membership: ClinicStaff,
    db: Annotated[AsyncSession, Depends(get_db)],
    patient_id: uuid.UUID | None = None,
    status: str | None = None,
    q: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int | None = Query(None, ge=1, le=100),
    sort: str | None = None,
) -> LoaRequestListResponse:
    rows, total = await loa_service.list_loa_requests(
        db,
        clinic_id,
        membership,
        patient_id=patient_id,
        status=status,
        q=q,
        page=page,
        page_size=page_size,
        sort=sort,
    )
    names = await loa_service.loa_patient_names(db, rows)
    items = [_to_read(r, names) for r in rows]
    return LoaRequestListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size or total or len(items),
    )


@router.post("", response_model=LoaRequestRead)
async def create_loa_request(
    data: LoaRequestCreate,
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    membership: ClinicStaff,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> LoaRequestRead:
    loa = await loa_service.create_loa_request(db, clinic_id, data, user, membership)
    names = await loa_service.loa_patient_names(db, [loa])
    return _to_read(loa, names)


@router.patch("/{loa_id}", response_model=LoaRequestRead)
async def patch_loa_request(
    loa_id: uuid.UUID,
    data: LoaRequestUpdate,
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    membership: ClinicStaff,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> LoaRequestRead:
    loa = await loa_service.update_loa_request(db, clinic_id, loa_id, data, user, membership)
    names = await loa_service.loa_patient_names(db, [loa])
    return _to_read(loa, names)

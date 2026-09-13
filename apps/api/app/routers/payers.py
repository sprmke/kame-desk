import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import ClinicStaff
from app.core.security import get_active_clinic_membership
from app.models import ClinicMembership
from app.schemas.payer_workflow import PayerCreate, PayerRead, PayerUpdate
from app.services import payer_service

router = APIRouter(prefix="/payers", tags=["payers"])


async def _clinic_id(
    membership: Annotated[ClinicMembership, Depends(get_active_clinic_membership)],
) -> uuid.UUID:
    return membership.clinic_id


@router.get("", response_model=list[PayerRead])
async def list_payers(
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    membership: ClinicStaff,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[PayerRead]:
    payers = await payer_service.list_payers(db, clinic_id, membership)
    return [PayerRead.model_validate(p) for p in payers]


@router.post("", response_model=PayerRead)
async def create_payer(
    data: PayerCreate,
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    membership: ClinicStaff,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PayerRead:
    payer = await payer_service.create_payer(db, clinic_id, data, membership)
    return PayerRead.model_validate(payer)


@router.patch("/{payer_id}", response_model=PayerRead)
async def patch_payer(
    payer_id: uuid.UUID,
    data: PayerUpdate,
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    membership: ClinicStaff,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PayerRead:
    payer = await payer_service.update_payer(db, clinic_id, payer_id, data, membership)
    return PayerRead.model_validate(payer)

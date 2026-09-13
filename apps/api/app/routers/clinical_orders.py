import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import ClinicStaff
from app.core.security import get_active_clinic_membership, get_current_user
from app.models import ClinicMembership, User
from app.schemas.clinical_order import ClinicalOrderCreate, ClinicalOrderRead, ClinicalOrderUpdate
from app.services import clinical_order_service

router = APIRouter(prefix="/patients/{patient_id}/orders", tags=["clinical-orders"])


async def _clinic_id(
    membership: Annotated[ClinicMembership, Depends(get_active_clinic_membership)],
) -> uuid.UUID:
    return membership.clinic_id


@router.get("", response_model=list[ClinicalOrderRead])
async def list_orders(
    patient_id: uuid.UUID,
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    membership: ClinicStaff,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[ClinicalOrderRead]:
    rows = await clinical_order_service.list_orders(db, clinic_id, patient_id)
    return [ClinicalOrderRead.model_validate(r) for r in rows]


@router.post("", response_model=ClinicalOrderRead)
async def create_order(
    patient_id: uuid.UUID,
    data: ClinicalOrderCreate,
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    membership: ClinicStaff,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ClinicalOrderRead:
    order = await clinical_order_service.create_order(db, clinic_id, patient_id, data, user.id)
    return ClinicalOrderRead.model_validate(order)


@router.patch("/{order_id}", response_model=ClinicalOrderRead)
async def patch_order(
    patient_id: uuid.UUID,
    order_id: uuid.UUID,
    data: ClinicalOrderUpdate,
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    membership: ClinicStaff,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ClinicalOrderRead:
    order = await clinical_order_service.update_order(db, clinic_id, order_id, data, user.id)
    return ClinicalOrderRead.model_validate(order)

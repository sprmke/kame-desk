import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import ClinicStaff
from app.core.security import get_active_clinic_membership, get_current_user
from app.models import ClinicMembership, Patient, User
from app.services.reminder_service import (
    list_clinic_reminders,
    retry_reminder,
    search_clinic_reminders,
)

router = APIRouter(prefix="/reminders", tags=["reminders"])


class ReminderRead(BaseModel):
    id: uuid.UUID
    appointment_id: uuid.UUID
    patient_id: uuid.UUID
    channel: str
    reminder_type: str
    scheduled_send_at: datetime
    sent_at: datetime | None
    status: str
    patient_name: str | None = None

    model_config = {"from_attributes": True}


class ReminderListResponse(BaseModel):
    items: list[ReminderRead]
    total: int
    page: int
    page_size: int


async def _clinic_id(
    membership: Annotated[ClinicMembership, Depends(get_active_clinic_membership)],
) -> uuid.UUID:
    return membership.clinic_id


@router.get("", response_model=list[ReminderRead])
async def list_reminders(
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    membership: ClinicStaff,
    db: Annotated[AsyncSession, Depends(get_db)],
    status: str | None = None,
) -> list[ReminderRead]:
    rows = await list_clinic_reminders(db, clinic_id, status=status)
    names: dict[uuid.UUID, str] = {}
    if rows:
        result = await db.execute(
            select(Patient).where(Patient.id.in_({r.patient_id for r in rows}))
        )
        names = {p.id: p.full_name for p in result.scalars().all()}
    out: list[ReminderRead] = []
    for row in rows:
        item = ReminderRead.model_validate(row)
        item.patient_name = names.get(row.patient_id)
        out.append(item)
    return out


@router.get("/search", response_model=ReminderListResponse)
async def search_reminders(
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    membership: ClinicStaff,
    db: Annotated[AsyncSession, Depends(get_db)],
    status: str | None = None,
    q: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    sort: str | None = None,
) -> ReminderListResponse:
    rows, total = await search_clinic_reminders(
        db,
        clinic_id,
        status=status,
        q=q,
        page=page,
        page_size=page_size,
        sort=sort,
    )
    return ReminderListResponse(
        items=[
            ReminderRead.model_validate(reminder).model_copy(update={"patient_name": patient_name})
            for reminder, patient_name in rows
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/{reminder_id}/retry", response_model=ReminderRead)
async def post_retry(
    reminder_id: uuid.UUID,
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    membership: ClinicStaff,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ReminderRead:
    row = await retry_reminder(db, clinic_id, reminder_id, user.id)
    return ReminderRead.model_validate(row)

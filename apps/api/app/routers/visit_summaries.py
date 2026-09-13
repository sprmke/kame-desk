import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import ClinicStaff
from app.core.security import get_active_clinic_membership, get_current_user
from app.models import ClinicMembership, User
from app.services.visit_summary_service import (
    approve_visit_summary,
    generate_visit_summary_draft,
    get_visit_summary,
    suppress_visit_summary,
)

router = APIRouter(tags=["visit-summaries"])


class VisitSummaryRead(BaseModel):
    id: uuid.UUID
    appointment_id: uuid.UUID
    generated_text: str
    generation_failed: bool = False
    edited_text: str | None
    status: str
    sent_at: str | None

    model_config = {"from_attributes": True}


class VisitSummaryApprove(BaseModel):
    edited_text: str | None = Field(default=None, max_length=8000)


def _read(row) -> VisitSummaryRead:
    return VisitSummaryRead(
        id=row.id,
        appointment_id=row.appointment_id,
        generated_text=row.generated_text,
        generation_failed=bool(row.generation_failed),
        edited_text=row.edited_text,
        status=row.status,
        sent_at=row.sent_at.isoformat() if row.sent_at else None,
    )


async def _clinic_id(
    membership: Annotated[ClinicMembership, Depends(get_active_clinic_membership)],
) -> uuid.UUID:
    return membership.clinic_id


@router.get("/appointments/{appointment_id}/visit-summary", response_model=VisitSummaryRead | None)
async def get_appointment_visit_summary(
    appointment_id: uuid.UUID,
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    membership: ClinicStaff,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> VisitSummaryRead | None:
    row = await get_visit_summary(db, clinic_id, appointment_id, membership)
    if row is None:
        return None
    return _read(row)


@router.post(
    "/appointments/{appointment_id}/visit-summary/generate", response_model=VisitSummaryRead
)
async def post_generate_visit_summary(
    appointment_id: uuid.UUID,
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    membership: ClinicStaff,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> VisitSummaryRead:
    row = await generate_visit_summary_draft(db, clinic_id, appointment_id, user, membership)
    return _read(row)


@router.post(
    "/appointments/{appointment_id}/visit-summary/approve", response_model=VisitSummaryRead
)
async def post_approve_visit_summary(
    appointment_id: uuid.UUID,
    data: VisitSummaryApprove,
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    membership: ClinicStaff,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> VisitSummaryRead:
    row = await approve_visit_summary(
        db, clinic_id, appointment_id, user, membership, data.edited_text
    )
    return _read(row)


@router.post(
    "/appointments/{appointment_id}/visit-summary/suppress", response_model=VisitSummaryRead
)
async def post_suppress_visit_summary(
    appointment_id: uuid.UUID,
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    membership: ClinicStaff,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> VisitSummaryRead:
    row = await suppress_visit_summary(db, clinic_id, appointment_id, user, membership)
    return _read(row)

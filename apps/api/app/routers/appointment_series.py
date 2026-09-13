import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import ClinicStaff
from app.core.security import get_active_clinic_membership, get_current_user
from app.models import ClinicMembership, User
from app.schemas.series import (
    AppointmentSeriesCreate,
    AppointmentSeriesCreateResponse,
    AppointmentSeriesRead,
    SeriesExpansionResult,
)
from app.services.clinic_service import get_clinic
from app.services.recurring_service import create_appointment_series

router = APIRouter(prefix="/appointment-series", tags=["appointment-series"])


async def _clinic_id(
    membership: Annotated[ClinicMembership, Depends(get_active_clinic_membership)],
) -> uuid.UUID:
    return membership.clinic_id


@router.post("", response_model=AppointmentSeriesCreateResponse)
async def post_appointment_series(
    data: AppointmentSeriesCreate,
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    membership: ClinicStaff,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AppointmentSeriesCreateResponse:
    clinic = await get_clinic(db, clinic_id)
    series, expansion = await create_appointment_series(
        db,
        clinic,
        patient_id=data.patient_id,
        doctor_id=data.doctor_id,
        rrule_string=data.rrule_string,
        series_start=data.series_start,
        duration_minutes=data.duration_minutes,
        actor_id=user.id,
        series_end=data.series_end,
        reason_for_visit=data.reason_for_visit,
    )
    return AppointmentSeriesCreateResponse(
        series=AppointmentSeriesRead.model_validate(series),
        expansion=SeriesExpansionResult.model_validate(expansion),
    )

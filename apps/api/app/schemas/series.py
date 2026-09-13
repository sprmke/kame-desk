import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.patient import PatientCreate


class WalkInCreate(BaseModel):
    doctor_id: uuid.UUID
    patient_id: uuid.UUID | None = None
    new_patient: PatientCreate | None = None
    reason_for_visit: str | None = Field(default=None, max_length=512)


class AppointmentSeriesCreate(BaseModel):
    patient_id: uuid.UUID
    doctor_id: uuid.UUID
    rrule_string: str = Field(min_length=1, max_length=512)
    series_start: datetime
    duration_minutes: int = Field(default=30, ge=5, le=480)
    series_end: datetime | None = None
    reason_for_visit: str | None = Field(default=None, max_length=512)


class SeriesConflict(BaseModel):
    occurrence_index: int
    scheduled_start: str
    detail: str


class SeriesExpansionResult(BaseModel):
    created: int
    conflicts: list[SeriesConflict]
    queued: bool = False


class AppointmentSeriesRead(BaseModel):
    id: uuid.UUID
    clinic_id: uuid.UUID
    patient_id: uuid.UUID
    doctor_id: uuid.UUID
    rrule_string: str
    series_start: datetime
    series_end: datetime | None
    duration_minutes: int
    reason_for_visit: str | None

    model_config = {"from_attributes": True}


class AppointmentSeriesCreateResponse(BaseModel):
    series: AppointmentSeriesRead
    expansion: SeriesExpansionResult

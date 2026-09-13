import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

AppointmentStatus = Literal["Scheduled", "Confirmed", "Cancelled", "No Show", "Rescheduled"]


class AppointmentCreate(BaseModel):
    patient_id: uuid.UUID
    doctor_id: uuid.UUID
    room_id: uuid.UUID | None = None
    service_fee_id: uuid.UUID | None = None
    scheduled_start: datetime
    scheduled_end: datetime
    reason_for_visit: str | None = Field(default=None, max_length=512)
    notes: str | None = None


class AppointmentUpdate(BaseModel):
    patient_id: uuid.UUID | None = None
    doctor_id: uuid.UUID | None = None
    room_id: uuid.UUID | None = None
    service_fee_id: uuid.UUID | None = None
    scheduled_start: datetime | None = None
    scheduled_end: datetime | None = None
    reason_for_visit: str | None = Field(default=None, max_length=512)
    notes: str | None = None
    appointment_status: AppointmentStatus | None = None


class NoShowRiskRead(BaseModel):
    level: str
    score: int
    reasons: list[str]


class AppointmentRead(BaseModel):
    id: uuid.UUID
    clinic_id: uuid.UUID
    patient_id: uuid.UUID
    doctor_id: uuid.UUID
    room_id: uuid.UUID | None
    service_fee_id: uuid.UUID | None = None
    booking_source: str = "staff"
    scheduled_start: datetime
    scheduled_end: datetime
    reason_for_visit: str | None
    notes: str | None
    appointment_status: str
    patient_name: str | None = None
    doctor_name: str | None = None
    room_name: str | None = None
    current_visit_status: str | None = None
    series_id: uuid.UUID | None = None
    series_occurrence_index: int | None = None
    no_show_risk: NoShowRiskRead | None = None

    model_config = {"from_attributes": True}


class AppointmentListResponse(BaseModel):
    items: list[AppointmentRead]
    total: int
    page: int = 1
    page_size: int = 0


class AppointmentConflict(BaseModel):
    detail: str = "Time slot unavailable"
    conflicting_appointment_id: uuid.UUID | None = None


class AppointmentReschedule(BaseModel):
    scheduled_start: datetime
    scheduled_end: datetime


class AvailableSlot(BaseModel):
    scheduled_start: str
    scheduled_end: str


class AvailableSlotList(BaseModel):
    slots: list[AvailableSlot]


class WaitlistCreate(BaseModel):
    patient_id: uuid.UUID
    doctor_id: uuid.UUID | None = None
    preferred_date: date | None = None
    notes: str | None = Field(default=None, max_length=512)


class WaitlistUpdate(BaseModel):
    doctor_id: uuid.UUID | None = None
    preferred_date: date | None = None
    notes: str | None = Field(default=None, max_length=512)
    status: Literal["waiting", "booked", "cancelled"] | None = None


class WaitlistRead(BaseModel):
    id: uuid.UUID
    clinic_id: uuid.UUID
    patient_id: uuid.UUID
    doctor_id: uuid.UUID | None
    preferred_date: date | None
    notes: str | None
    status: str
    booked_appointment_id: uuid.UUID | None
    created_at: datetime
    patient_name: str | None = None
    doctor_name: str | None = None

    model_config = {"from_attributes": True}

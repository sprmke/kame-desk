import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class PublicDoctorRead(BaseModel):
    id: uuid.UUID
    specialty: str | None
    full_name: str


class PublicClinicRead(BaseModel):
    name: str
    slug: str
    address: str | None
    contact_phone: str | None
    contact_email: str | None
    working_hours: dict | None
    holiday_dates: list[str]
    default_appointment_duration_minutes: int
    doctors: list[PublicDoctorRead]
    services: list[dict[str, str]]


class PublicSlot(BaseModel):
    scheduled_start: str
    scheduled_end: str


class PublicSlotList(BaseModel):
    slots: list[PublicSlot]


class PublicAppointmentRequest(BaseModel):
    doctor_id: uuid.UUID
    full_name: str = Field(min_length=1, max_length=255)
    contact_number: str = Field(min_length=1, max_length=50)
    email: EmailStr | None = None
    scheduled_start: datetime
    scheduled_end: datetime
    reason_for_visit: str | None = Field(default=None, max_length=512)

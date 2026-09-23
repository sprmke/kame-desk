import uuid
from datetime import date, datetime

from pydantic import BaseModel, EmailStr, Field


class PublicDoctorRead(BaseModel):
    id: uuid.UUID
    specialty: str | None
    full_name: str


class PublicServiceRead(BaseModel):
    id: uuid.UUID
    name: str
    amount: str
    duration_minutes: int | None = None


class PublicClinicRead(BaseModel):
    name: str
    slug: str
    address: str | None
    contact_phone: str | None
    contact_email: str | None
    working_hours: dict | None
    holiday_dates: list[str]
    default_appointment_duration_minutes: int
    advance_booking_days: int = 90
    cancellation_notice_hours: int = 0
    public_intake_fields: dict[str, bool]
    doctors: list[PublicDoctorRead]
    services: list[PublicServiceRead]


class PublicSlot(BaseModel):
    scheduled_start: str
    scheduled_end: str


class PublicSlotList(BaseModel):
    slots: list[PublicSlot]


class PublicAppointmentRequest(BaseModel):
    doctor_id: uuid.UUID
    service_fee_id: uuid.UUID | None = None
    full_name: str = Field(min_length=1, max_length=255)
    contact_number: str = Field(min_length=1, max_length=50)
    email: EmailStr | None = None
    birthdate: date | None = None
    sex: str | None = Field(default=None, max_length=16)
    address: str | None = None
    scheduled_start: datetime
    scheduled_end: datetime
    reason_for_visit: str | None = Field(default=None, max_length=512)
    notes: str | None = None
    is_existing_patient: bool | None = None

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, EmailStr, Field


class ClinicUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    logo_url: str | None = None
    brand_color: str | None = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")
    address: str | None = None
    contact_phone: str | None = None
    contact_email: EmailStr | None = None
    license_info: str | None = None
    accreditation_info: str | None = None
    default_appointment_duration_minutes: int | None = Field(default=None, ge=5, le=480)
    public_booking_auto_confirm: bool | None = None
    reception_can_view_soap: bool | None = None
    recording_consent_enabled: bool | None = None
    ai_assistant_enabled: bool | None = None
    assistant_disabled_tools: list[str] | None = None


class WorkingHoursDay(BaseModel):
    open: str
    close: str
    closed: bool = False


class WorkingHoursUpdate(BaseModel):
    working_hours: dict[str, WorkingHoursDay]
    holiday_dates: list[str] = Field(default_factory=list)


class ReceiptNumberingRead(BaseModel):
    prefix: str
    next_number: int
    pad_width: int


class ReceiptNumberingUpdate(BaseModel):
    prefix: str = Field(min_length=1, max_length=16, pattern=r"^[A-Za-z0-9\-]+$")
    next_number: int = Field(ge=1, le=99_999_999)
    pad_width: int = Field(ge=1, le=10)


class BirComplianceRead(BaseModel):
    tin: str | None = None
    registered_name: str | None = None
    registered_address: str | None = None
    vat_registered: bool = False
    compliance_mode: Literal["not_yet_accredited", "ptu", "cas"] = "not_yet_accredited"
    accreditation_number: str | None = None
    accreditation_valid_until: str | None = None


class BirComplianceUpdate(BaseModel):
    tin: str | None = Field(default=None, max_length=32)
    registered_name: str | None = Field(default=None, max_length=255)
    registered_address: str | None = Field(default=None, max_length=512)
    vat_registered: bool = False
    compliance_mode: Literal["not_yet_accredited", "ptu", "cas"] = "not_yet_accredited"
    accreditation_number: str | None = Field(default=None, max_length=128)
    accreditation_valid_until: str | None = Field(default=None, max_length=10)


class GrowthSettingsRead(BaseModel):
    google_review_link: str | None = None
    review_requests_enabled: bool = False
    doh_accreditation_number: str | None = None
    doh_accreditation_valid_until: str | None = None


class GrowthSettingsUpdate(BaseModel):
    google_review_link: str | None = Field(default=None, max_length=2048)
    review_requests_enabled: bool = False
    doh_accreditation_number: str | None = Field(default=None, max_length=128)
    doh_accreditation_valid_until: str | None = Field(default=None, max_length=10)


class SeatSummaryRead(BaseModel):
    limit: int | None
    used: int
    remaining: int | None


class ClinicRead(BaseModel):
    id: uuid.UUID
    name: str
    logo_url: str | None
    brand_color: str | None = None
    address: str | None
    contact_phone: str | None
    contact_email: str | None
    timezone: str
    license_info: str | None
    accreditation_info: str | None
    working_hours: dict[str, Any] | None
    holiday_dates: list[str] | None
    default_appointment_duration_minutes: int
    onboarding_completed_at: datetime | None
    slug: str
    public_booking_auto_confirm: bool
    reception_can_view_soap: bool
    recording_consent_enabled: bool
    ai_assistant_enabled: bool
    assistant_disabled_tools: list[str] = Field(default_factory=list)
    status: str = "active"
    plan_key: str | None = "starter"
    organization_id: uuid.UUID | None = None
    deletion_requested_at: datetime | None = None
    receipt_numbering: ReceiptNumberingRead | None = None
    bir_compliance: BirComplianceRead | None = None
    growth_settings: GrowthSettingsRead | None = None

    model_config = {"from_attributes": True}


class DoctorProfileCreate(BaseModel):
    user_id: uuid.UUID | None = None
    email: EmailStr | None = None
    full_name: str | None = None
    specialty: str = Field(min_length=1, max_length=128)
    prc_license_number: str = Field(min_length=1, max_length=64)
    consultation_fee: Decimal = Field(ge=0)
    follow_up_fee: Decimal | None = Field(default=None, ge=0)
    default_appointment_duration_minutes: int | None = Field(default=None, ge=5, le=480)


class DoctorProfileUpdate(BaseModel):
    specialty: str | None = None
    prc_license_number: str | None = None
    consultation_fee: Decimal | None = Field(default=None, ge=0)
    follow_up_fee: Decimal | None = Field(default=None, ge=0)
    default_appointment_duration_minutes: int | None = Field(default=None, ge=5, le=480)
    photo_url: str | None = None


class DoctorProfileRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    clinic_id: uuid.UUID
    specialty: str | None
    prc_license_number: str | None
    signature_image_key: str | None
    photo_url: str | None
    consultation_fee: Decimal | None
    follow_up_fee: Decimal | None
    default_appointment_duration_minutes: int | None
    full_name: str | None = None
    email: str | None = None

    model_config = {"from_attributes": True}


class ServiceFeeCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    amount: Decimal = Field(ge=0)
    category: str | None = Field(default=None, max_length=64)
    duration_minutes: int | None = Field(default=None, ge=5, le=480)


class ServiceFeeUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    amount: Decimal | None = Field(default=None, ge=0)
    category: str | None = None
    duration_minutes: int | None = Field(default=None, ge=5, le=480)


class ServiceFeeRead(BaseModel):
    id: uuid.UUID
    clinic_id: uuid.UUID
    name: str
    amount: Decimal
    category: str | None
    duration_minutes: int | None = None

    model_config = {"from_attributes": True}


class RoomCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)


class RoomUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    is_active: bool | None = None


class RoomRead(BaseModel):
    id: uuid.UUID
    clinic_id: uuid.UUID
    name: str
    is_active: bool

    model_config = {"from_attributes": True}


class InvitationCreate(BaseModel):
    email: EmailStr
    role: str = Field(pattern="^(admin|doctor|reception)$")
    full_name: str | None = None
    doctor_profile: DoctorProfileCreate | None = None


class InvitationRead(BaseModel):
    id: uuid.UUID
    email: str
    role: str
    expires_at: datetime
    accepted_at: datetime | None
    revoked_at: datetime | None

    model_config = {"from_attributes": True}


class InvitationAccept(BaseModel):
    full_name: str | None = None
    password: str | None = Field(default=None, min_length=8)


class OnboardingStepStatus(BaseModel):
    key: str
    label: str
    complete: bool


class OnboardingStatusRead(BaseModel):
    steps: list[OnboardingStepStatus]
    all_complete: bool
    current_step: str | None


class PresignedUploadRequest(BaseModel):
    content_type: str = Field(pattern="^image/(png|jpeg|webp)$")
    file_size_bytes: int = Field(ge=1, le=2_000_000)


class PresignedUploadResponse(BaseModel):
    upload_url: str
    object_key: str
    expires_in_seconds: int = 300


class MembershipRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    email: str
    full_name: str
    role: str
    is_active: bool

    model_config = {"from_attributes": True}


class MembershipUpdate(BaseModel):
    role: str | None = Field(default=None, pattern="^(owner|admin|doctor|reception)$")
    is_active: bool | None = None

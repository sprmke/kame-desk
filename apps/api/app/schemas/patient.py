import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, EmailStr, Field


class EmergencyContact(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    relationship: str = Field(min_length=1, max_length=64)
    number: str = Field(min_length=1, max_length=50)


class InsuranceInfo(BaseModel):
    provider: str | None = None
    member_id: str | None = None
    coverage_notes: str | None = None


class PatientCreate(BaseModel):
    data_processing_consent: bool | None = None
    full_name: str = Field(min_length=1, max_length=255)
    birthdate: date | None = None
    sex: str | None = Field(default=None, max_length=16)
    civil_status: str | None = Field(default=None, max_length=32)
    occupation: str | None = Field(default=None, max_length=128)
    contact_number: str | None = Field(default=None, max_length=50)
    email: EmailStr | None = None
    address: str | None = None
    emergency_contact: EmergencyContact | None = None
    insurance_info: InsuranceInfo | None = None


class PatientUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    birthdate: date | None = None
    sex: str | None = Field(default=None, max_length=16)
    civil_status: str | None = Field(default=None, max_length=32)
    occupation: str | None = Field(default=None, max_length=128)
    contact_number: str | None = Field(default=None, max_length=50)
    email: EmailStr | None = None
    address: str | None = None
    emergency_contact: EmergencyContact | None = None
    insurance_info: InsuranceInfo | None = None
    is_archived: bool | None = None
    reminders_opted_out: bool | None = None


class PatientRead(BaseModel):
    id: uuid.UUID
    clinic_id: uuid.UUID
    patient_number: int
    full_name: str
    birthdate: date | None
    sex: str | None
    civil_status: str | None
    occupation: str | None
    contact_number: str | None
    email: str | None
    address: str | None
    emergency_contact: dict[str, Any] | None
    insurance_info: dict[str, Any] | None
    is_archived: bool
    no_show_count: int = 0
    reminders_opted_out: bool = False
    data_processing_consent_at: datetime | None = None

    model_config = {"from_attributes": True}


class PatientListResponse(BaseModel):
    items: list[PatientRead]
    total: int
    page: int
    page_size: int


class AllergyEntry(BaseModel):
    substance: str = Field(min_length=1, max_length=255)
    reaction: str | None = Field(default=None, max_length=255)
    severity: Literal["mild", "moderate", "severe"] | None = None


class MedicationEntry(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    dose: str | None = None
    frequency: str | None = None


class MedicalInfoUpdate(BaseModel):
    allergies_reviewed: bool
    allergies: list[AllergyEntry] = Field(default_factory=list)
    medical_history: str | None = None
    family_history: str | None = None
    surgical_history: str | None = None
    current_medications: list[MedicationEntry] = Field(default_factory=list)
    chronic_conditions: list[str] = Field(default_factory=list)
    vaccination_history: list[str] = Field(default_factory=list)
    clinical_notes: str | None = None


class MedicalInfoRead(BaseModel):
    allergies_reviewed: bool
    allergies: list[dict[str, Any]]
    medical_history: str | None
    family_history: str | None
    surgical_history: str | None
    current_medications: list[dict[str, Any]]
    chronic_conditions: list[str]
    vaccination_history: list[str]
    clinical_notes: str | None

    model_config = {"from_attributes": True}


class VitalsCreate(BaseModel):
    recorded_at: datetime | None = None
    height_cm: Decimal | None = Field(default=None, ge=0)
    weight_kg: Decimal | None = Field(default=None, ge=0)
    blood_pressure: str | None = Field(default=None, max_length=16)
    temperature_c: Decimal | None = Field(default=None, ge=30, le=45)
    heart_rate: int | None = Field(default=None, ge=0, le=300)
    respiratory_rate: int | None = Field(default=None, ge=0, le=100)
    spo2: int | None = Field(default=None, ge=0, le=100)
    visit_id: uuid.UUID | None = None


class VitalsRead(BaseModel):
    id: uuid.UUID
    recorded_at: datetime
    height_cm: Decimal | None
    weight_kg: Decimal | None
    bmi: Decimal | None
    blood_pressure: str | None
    temperature_c: Decimal | None
    heart_rate: int | None
    respiratory_rate: int | None
    spo2: int | None
    visit_id: uuid.UUID | None

    model_config = {"from_attributes": True}


class PatientFileCreate(BaseModel):
    content_type: str = Field(pattern=r"^(image/(png|jpeg|webp)|application/pdf)$")
    file_size_bytes: int = Field(ge=1, le=20_000_000)
    file_type: Literal[
        "lab_result", "xray", "ultrasound", "mri_ct", "image", "pdf", "clinical_document", "other"
    ]
    description: str | None = None
    visit_id: uuid.UUID | None = None


class PatientFileRead(BaseModel):
    id: uuid.UUID
    file_type: str
    description: str | None
    uploaded_at: datetime
    visit_id: uuid.UUID | None
    download_url: str | None = None

    model_config = {"from_attributes": True}


class PatientFileUploadResponse(BaseModel):
    file_id: uuid.UUID
    upload_url: str
    object_key: str


class PatientMergeRequest(BaseModel):
    source_patient_id: uuid.UUID


class PatientImportRequest(BaseModel):
    csv: str = Field(min_length=1)
    commit: bool = False


class PatientImportResponse(BaseModel):
    items: list[dict]
    errors: list[str]
    created: int
    committed: bool

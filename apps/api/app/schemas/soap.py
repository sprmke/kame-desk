import uuid
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field


class SoapNoteCreate(BaseModel):
    subjective: str | None = None
    objective: str | None = None
    assessment: str | None = None
    plan: str | None = None
    diagnosis_primary: str | None = Field(default=None, max_length=512)
    diagnosis_secondary: list[str] | None = None
    icd10_codes: list[str] | None = None
    follow_up_date: date | None = None
    specialty_template_key: str | None = Field(default=None, max_length=64)
    specialty_data: dict[str, Any] | None = None
    client_draft_token: str | None = Field(default=None, max_length=64)


class SoapNoteRead(BaseModel):
    id: uuid.UUID
    appointment_id: uuid.UUID
    patient_id: uuid.UUID
    doctor_id: uuid.UUID
    clinic_id: uuid.UUID
    version_number: int
    subjective: str | None
    objective: str | None
    assessment: str | None
    plan: str | None
    diagnosis_primary: str | None
    diagnosis_secondary: list[str] | None
    icd10_codes: list[str] | None
    follow_up_date: date | None
    specialty_template_key: str | None
    specialty_data: dict[str, Any] | None
    signed_at: datetime | None
    signature_image_url: str | None
    created_by_user_id: uuid.UUID
    created_at: datetime
    author_name: str | None = None
    client_draft_token: str | None = None

    model_config = {"from_attributes": True}


class SoapNoteListResponse(BaseModel):
    items: list[SoapNoteRead]
    latest_version: int | None = None


class SpecialtyTemplateRead(BaseModel):
    template_key: str
    name: str
    schema_version: int
    description: str | None = None


class SoapDraftRequest(BaseModel):
    input_text: str = Field(min_length=1, max_length=2000)

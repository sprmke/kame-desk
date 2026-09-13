import uuid
from datetime import datetime

from pydantic import BaseModel, Field

DOCUMENT_TYPES = (
    "medical_certificate",
    "referral_letter",
    "lab_request",
    "confinement_certificate",
    "custom",
)


class DocumentTemplateCreate(BaseModel):
    template_key: str = Field(min_length=1, max_length=64, pattern=r"^[a-z0-9_]+$")
    name: str = Field(min_length=1, max_length=128)
    template_type: str = Field(
        pattern=r"^(medical_certificate|referral_letter|lab_request|confinement_certificate|custom)$"
    )
    body_template: str = Field(min_length=1)
    is_active: bool = True


class DocumentTemplateUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    body_template: str | None = Field(default=None, min_length=1)
    is_active: bool | None = None


class DocumentTemplatePreviewRequest(BaseModel):
    body_template: str = Field(min_length=1)


class DocumentTemplatePreviewRead(BaseModel):
    placeholders: list[str]
    preview: str


class DocumentTemplateRead(BaseModel):
    id: uuid.UUID
    clinic_id: uuid.UUID | None
    template_key: str
    name: str
    template_type: str
    body_template: str | None
    is_active: bool

    model_config = {"from_attributes": True}


class GeneratedDocumentCreate(BaseModel):
    template_id: uuid.UUID
    appointment_id: uuid.UUID | None = None
    extra_context: dict[str, str] = Field(default_factory=dict)
    referral_recipient: str | None = Field(default=None, max_length=255)


class GeneratedDocumentRead(BaseModel):
    id: uuid.UUID
    clinic_id: uuid.UUID
    patient_id: uuid.UUID
    appointment_id: uuid.UUID | None
    template_id: uuid.UUID
    document_type: str
    status: str
    preview_content: str
    final_content_snapshot: str | None
    patient_file_id: uuid.UUID | None
    issued_at: datetime | None
    created_at: datetime
    template_name: str | None = None
    referral_recipient: str | None = None
    referral_status: str | None = None
    referral_outcome: str | None = None
    chart_share_expires_at: datetime | None = None

    model_config = {"from_attributes": True}


class ChartShareRead(BaseModel):
    share_url: str
    expires_at: datetime


class GeneratedDocumentUpdate(BaseModel):
    referral_recipient: str | None = Field(default=None, max_length=255)
    referral_status: str | None = Field(
        default=None, pattern=r"^(draft|sent|acknowledged|completed)$"
    )
    referral_outcome: str | None = None


class GeneratedDocumentListResponse(BaseModel):
    items: list[GeneratedDocumentRead]
    total: int

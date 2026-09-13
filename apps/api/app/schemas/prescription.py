import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class PrescriptionItemCreate(BaseModel):
    drug_name: str = Field(min_length=1, max_length=256)
    generic_name: str | None = Field(default=None, max_length=256)
    dosage: str | None = Field(default=None, max_length=128)
    form: str | None = Field(default=None, max_length=64)
    frequency: str | None = Field(default=None, max_length=128)
    duration: str | None = Field(default=None, max_length=128)
    quantity: str | None = Field(default=None, max_length=64)
    special_instructions: str | None = None


class PrescriptionCreate(BaseModel):
    appointment_id: uuid.UUID | None = None
    notes: str | None = None
    items: list[PrescriptionItemCreate] = Field(min_length=1)


class PrescriptionItemRead(BaseModel):
    id: uuid.UUID
    drug_name: str
    generic_name: str | None
    dosage: str | None
    form: str | None
    frequency: str | None
    duration: str | None
    quantity: str | None
    special_instructions: str | None
    sort_order: int

    model_config = {"from_attributes": True}


class ConflictFlagRead(BaseModel):
    type: str
    drug_name: str
    message: str
    related: str | None = None


class PrescriptionRead(BaseModel):
    id: uuid.UUID
    patient_id: uuid.UUID
    doctor_id: uuid.UUID
    clinic_id: uuid.UUID
    appointment_id: uuid.UUID | None
    status: str
    notes: str | None
    pdf_object_key: str | None
    issued_at: datetime | None
    voided_at: datetime | None
    void_reason: str | None
    override_reason: str | None
    conflict_flags: list[dict[str, Any]] | None
    created_by_user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    items: list[PrescriptionItemRead] = Field(default_factory=list)
    doctor_name: str | None = None
    pdf_download_url: str | None = None

    model_config = {"from_attributes": True}


class PrescriptionListResponse(BaseModel):
    items: list[PrescriptionRead]
    total: int


class PrescriptionIssue(BaseModel):
    override_reason: str | None = None


class PrescriptionVoid(BaseModel):
    reason: str = Field(min_length=1, max_length=2000)


class PrescriptionConflictCheck(BaseModel):
    drug_names: list[str] = Field(min_length=1)


class PrescriptionConflictResponse(BaseModel):
    flags: list[ConflictFlagRead]

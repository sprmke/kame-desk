import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ClinicalOrderCreate(BaseModel):
    order_type: Literal["lab", "imaging"]
    name: str = Field(min_length=1, max_length=255)
    appointment_id: uuid.UUID | None = None


class ClinicalOrderUpdate(BaseModel):
    status: Literal["ordered", "in_progress", "resulted", "cancelled"] | None = None
    result_summary: str | None = None
    patient_file_id: uuid.UUID | None = None


class ClinicalOrderRead(BaseModel):
    id: uuid.UUID
    clinic_id: uuid.UUID
    patient_id: uuid.UUID
    appointment_id: uuid.UUID | None
    order_type: str
    name: str
    status: str
    result_summary: str | None
    patient_file_id: uuid.UUID | None
    created_at: datetime

    model_config = {"from_attributes": True}

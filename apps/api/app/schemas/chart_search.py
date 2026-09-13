import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class RecordingCreate(BaseModel):
    content_type: str = Field(min_length=3, max_length=128)
    file_size_bytes: int = Field(gt=0, le=50_000_000)
    duration_seconds: int | None = Field(default=None, ge=0, le=7200)


class RecordingRead(BaseModel):
    id: uuid.UUID
    appointment_id: uuid.UUID
    clinic_id: uuid.UUID
    duration_seconds: int | None
    transcription_status: str
    transcript_text: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class RecordingUploadResponse(BaseModel):
    recording: RecordingRead
    upload_url: str
    object_key: str


class ChartSearchResult(BaseModel):
    soap_note_id: uuid.UUID
    appointment_id: uuid.UUID
    patient_id: uuid.UUID
    patient_name: str
    version_number: int
    snippet: str
    visit_date: datetime
    score: float


class ChartSearchResponse(BaseModel):
    items: list[ChartSearchResult]

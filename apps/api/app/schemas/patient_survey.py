import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class NpsRespondRequest(BaseModel):
    score: int = Field(ge=0, le=10)
    comment: str | None = Field(default=None, max_length=2000)


class PatientSurveyResponseRead(BaseModel):
    id: uuid.UUID
    patient_id: uuid.UUID
    visit_id: uuid.UUID
    score: int | None
    comment: str | None
    sent_at: datetime
    responded_at: datetime | None

    model_config = {"from_attributes": True}


class NpsReportRow(BaseModel):
    period: str
    sent: int
    responded: int
    promoters: int
    passives: int
    detractors: int
    nps_score: float | None


class NpsReportResponse(BaseModel):
    series: list[NpsReportRow]
    from_date: str
    to_date: str

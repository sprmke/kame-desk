from pydantic import BaseModel, Field

from app.schemas.prescription import ConflictFlagRead


class PrescriptionFlagExplainRequest(BaseModel):
    flag: ConflictFlagRead


class PrescriptionFlagExplainResponse(BaseModel):
    explanation: str
    flag: ConflictFlagRead


class BillingExtractionFieldRead(BaseModel):
    value: str | None
    confidence: str


class BillingExtractionDraftRead(BaseModel):
    amount: BillingExtractionFieldRead
    date: BillingExtractionFieldRead
    provider: BillingExtractionFieldRead
    reference_number: BillingExtractionFieldRead


class BillingExtractionResponse(BaseModel):
    attempt_id: str
    fields: BillingExtractionDraftRead
    source_preview_url: str | None = None


class BillingExtractionConfirm(BaseModel):
    attempt_id: str = Field(min_length=1)


class BillingExtractionRequest(BaseModel):
    filename: str = Field(min_length=1, max_length=255)
    content_type: str = Field(min_length=1, max_length=128)
    content_base64: str = Field(min_length=1)

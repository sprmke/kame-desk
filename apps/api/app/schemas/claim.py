import uuid
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

PayerType = Literal["hmo", "philhealth", "self_pay", "other"]


class InsuranceClaimCreate(BaseModel):
    patient_id: uuid.UUID
    invoice_id: uuid.UUID | None = None
    provider: str = Field(min_length=1, max_length=255)
    payer_type: PayerType = "hmo"
    member_id: str | None = Field(default=None, max_length=128)
    claim_reference: str | None = Field(default=None, max_length=128)
    amount: Decimal = Field(gt=0)
    notes: str | None = None
    loa_request_id: uuid.UUID | None = None


class InsuranceClaimUpdate(BaseModel):
    status: Literal["draft", "submitted", "approved", "denied", "paid"] | None = None
    payer_type: PayerType | None = None
    claim_reference: str | None = Field(default=None, max_length=128)
    amount: Decimal | None = Field(default=None, gt=0)
    notes: str | None = None
    provider: str | None = Field(default=None, min_length=1, max_length=255)
    member_id: str | None = Field(default=None, max_length=128)
    loa_request_id: uuid.UUID | None = None


class InsuranceClaimRead(BaseModel):
    id: uuid.UUID
    clinic_id: uuid.UUID
    patient_id: uuid.UUID
    invoice_id: uuid.UUID | None
    provider: str
    payer_type: PayerType
    member_id: str | None
    claim_reference: str | None
    amount: Decimal
    status: str
    notes: str | None
    loa_request_id: uuid.UUID | None
    created_at: datetime
    patient_name: str | None = None
    invoice_number: str | None = None

    model_config = {"from_attributes": True}


class InsuranceClaimListResponse(BaseModel):
    items: list[InsuranceClaimRead]
    total: int
    page: int = 1
    page_size: int = 0

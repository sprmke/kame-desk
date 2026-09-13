import uuid
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

PayerType = Literal["hmo", "philhealth", "self_pay", "other"]
EligibilityStatus = Literal["pending", "verified", "denied", "expired"]
LoaStatus = Literal["requested", "submitted", "approved", "denied"]


class PayerCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    payer_type: PayerType = "hmo"


class PayerUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    payer_type: PayerType | None = None
    is_active: bool | None = None


class PayerRead(BaseModel):
    id: uuid.UUID
    clinic_id: uuid.UUID
    name: str
    payer_type: PayerType
    is_active: bool

    model_config = {"from_attributes": True}


class EligibilityCheckCreate(BaseModel):
    patient_id: uuid.UUID
    payer_name: str = Field(min_length=1, max_length=255)
    payer_type: PayerType = "hmo"
    member_id: str | None = Field(default=None, max_length=128)
    notes: str | None = None


class EligibilityCheckUpdate(BaseModel):
    status: EligibilityStatus | None = None
    verified_amount: Decimal | None = Field(default=None, ge=0)
    notes: str | None = None


class EligibilityCheckRead(BaseModel):
    id: uuid.UUID
    clinic_id: uuid.UUID
    patient_id: uuid.UUID
    payer_name: str
    payer_type: PayerType
    member_id: str | None
    status: EligibilityStatus
    verified_amount: Decimal | None
    notes: str | None
    checked_by_user_id: uuid.UUID
    checked_at: datetime
    patient_name: str | None = None

    model_config = {"from_attributes": True}


class EligibilityCheckListResponse(BaseModel):
    items: list[EligibilityCheckRead]
    total: int
    page: int = 1
    page_size: int = 0


class LoaRequestCreate(BaseModel):
    patient_id: uuid.UUID
    claim_id: uuid.UUID | None = None
    hmo_name: str = Field(min_length=1, max_length=255)


class LoaRequestUpdate(BaseModel):
    status: LoaStatus | None = None
    claim_id: uuid.UUID | None = None
    reference_number: str | None = Field(default=None, max_length=128)
    document_object_key: str | None = Field(default=None, max_length=512)
    decision_notes: str | None = None


class LoaRequestRead(BaseModel):
    id: uuid.UUID
    clinic_id: uuid.UUID
    patient_id: uuid.UUID
    claim_id: uuid.UUID | None
    hmo_name: str
    status: LoaStatus
    reference_number: str | None
    document_object_key: str | None
    requested_by_user_id: uuid.UUID
    submitted_at: datetime | None
    decided_at: datetime | None
    decision_notes: str | None
    created_at: datetime
    patient_name: str | None = None

    model_config = {"from_attributes": True}


class LoaRequestListResponse(BaseModel):
    items: list[LoaRequestRead]
    total: int
    page: int = 1
    page_size: int = 0

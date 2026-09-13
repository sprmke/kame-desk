import uuid
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

LineCategory = Literal["consultation", "procedure", "lab", "medicine", "other"]
PaymentMethod = Literal["cash", "gcash", "card", "bank_transfer"]


class InvoiceLineItemCreate(BaseModel):
    description: str = Field(min_length=1, max_length=512)
    category: LineCategory = "other"
    quantity: Decimal = Field(default=Decimal("1"), gt=0)
    unit_price: Decimal = Field(ge=0)
    hmo_covered_amount: Decimal | None = Field(default=None, ge=0)
    hmo_claim_reference: str | None = Field(default=None, max_length=128)


class InvoiceLineItemUpdate(BaseModel):
    description: str | None = Field(default=None, min_length=1, max_length=512)
    category: LineCategory | None = None
    quantity: Decimal | None = Field(default=None, gt=0)
    unit_price: Decimal | None = Field(default=None, ge=0)
    hmo_covered_amount: Decimal | None = Field(default=None, ge=0)
    hmo_claim_reference: str | None = Field(default=None, max_length=128)


class InvoiceLineItemRead(BaseModel):
    id: uuid.UUID
    description: str
    category: str
    quantity: Decimal
    unit_price: Decimal
    amount: Decimal
    hmo_covered_amount: Decimal | None
    hmo_claim_reference: str | None
    sort_order: int

    model_config = {"from_attributes": True}


class InvoiceCreate(BaseModel):
    appointment_id: uuid.UUID | None = None
    line_items: list[InvoiceLineItemCreate] = Field(default_factory=list)


class CreditNoteRead(BaseModel):
    id: uuid.UUID
    invoice_id: uuid.UUID
    credit_number: str
    kind: str
    amount: Decimal
    reason: str
    created_at: datetime

    model_config = {"from_attributes": True}


class CreditNoteCreate(BaseModel):
    kind: Literal["refund", "adjustment"] = "refund"
    amount: Decimal = Field(gt=0)
    reason: str = Field(min_length=1, max_length=2000)


class InvoiceRead(BaseModel):
    id: uuid.UUID
    clinic_id: uuid.UUID
    patient_id: uuid.UUID
    appointment_id: uuid.UUID | None
    invoice_number: str | None
    status: str
    subtotal: Decimal
    total: Decimal
    void_reason: str | None
    issued_at: datetime | None
    voided_at: datetime | None
    created_by_user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    line_items: list[InvoiceLineItemRead] = Field(default_factory=list)
    amount_paid: Decimal = Decimal("0")
    balance_due: Decimal = Decimal("0")
    amount_credited: Decimal = Decimal("0")
    credit_notes: list[CreditNoteRead] = Field(default_factory=list)
    patient_name: str | None = None
    financing_status: str | None = None
    financing_available: bool = False

    model_config = {"from_attributes": True}


class InvoiceListResponse(BaseModel):
    items: list[InvoiceRead]
    total: int
    page: int = 1
    page_size: int = 0


class PaymentCreate(BaseModel):
    method: PaymentMethod
    amount: Decimal = Field(gt=0)
    reference_number: str | None = Field(default=None, max_length=128)
    paid_at: datetime | None = None


class PaymentRead(BaseModel):
    id: uuid.UUID
    invoice_id: uuid.UUID
    method: str
    amount: Decimal
    paid_at: datetime
    reference_number: str | None

    model_config = {"from_attributes": True}


class InvoiceVoid(BaseModel):
    reason: str = Field(min_length=1, max_length=2000)


class PatientBalanceRead(BaseModel):
    patient_id: uuid.UUID
    outstanding_balance: Decimal
    invoice_count: int


class OutstandingBalanceEntry(BaseModel):
    patient_id: uuid.UUID
    patient_name: str
    outstanding_balance: Decimal
    oldest_invoice_date: datetime | None


class OutstandingBalancesResponse(BaseModel):
    items: list[OutstandingBalanceEntry]
    total_outstanding: Decimal


class RevenueSummaryRead(BaseModel):
    today: Decimal
    week: Decimal
    month: Decimal

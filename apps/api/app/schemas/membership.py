import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field


class IncludedService(BaseModel):
    category: str = Field(min_length=1, max_length=64)
    count_per_period: int = Field(ge=1, le=999)


class MembershipPlanCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    price: Decimal = Field(ge=0)
    billing_interval: str = Field(pattern="^(monthly|quarterly|annual)$")
    included_services: list[IncludedService] = Field(default_factory=list)


class MembershipPlanUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    price: Decimal | None = Field(default=None, ge=0)
    billing_interval: str | None = Field(default=None, pattern="^(monthly|quarterly|annual)$")
    included_services: list[IncludedService] | None = None
    is_active: bool | None = None


class MembershipPlanRead(BaseModel):
    id: uuid.UUID
    clinic_id: uuid.UUID
    name: str
    price: Decimal
    billing_interval: str
    included_services: list[dict[str, Any]]
    is_active: bool

    model_config = {"from_attributes": True}


class PatientMembershipEnroll(BaseModel):
    plan_id: uuid.UUID


class PatientMembershipRead(BaseModel):
    id: uuid.UUID
    clinic_id: uuid.UUID
    patient_id: uuid.UUID
    plan_id: uuid.UUID
    plan_name: str | None = None
    status: str
    started_at: date
    current_period_end: date
    usage_this_period: dict[str, int]
    cancelled_at: datetime | None

    model_config = {"from_attributes": True}

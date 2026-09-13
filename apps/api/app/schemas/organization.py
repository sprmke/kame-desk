import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class OrganizationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class OrganizationRead(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    status: str
    is_owner: bool = False

    model_config = {"from_attributes": True}


class OrganizationSubscriptionRead(BaseModel):
    plan_key: str
    status: str
    trial_ends_at: datetime | None = None


class EnrolledClinicRead(BaseModel):
    id: uuid.UUID
    clinic_id: uuid.UUID
    clinic_name: str
    clinic_slug: str
    status: str
    enrolled_at: datetime | None = None


class OrganizationDetailRead(OrganizationRead):
    subscription: OrganizationSubscriptionRead | None = None
    enrolled_clinics: list[EnrolledClinicRead] = Field(default_factory=list)


class CreateClinicUnderOrgRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    slug: str | None = Field(default=None, max_length=64)


class CreateClinicUnderOrgResponse(BaseModel):
    clinic_id: uuid.UUID
    clinic_name: str
    clinic_slug: str
    enrollment_status: str
    organization_id: uuid.UUID


class OrgSeatSummaryRead(BaseModel):
    limit: int | None
    used: int
    remaining: int | None
    max_clinics: int | None
    enrolled_clinics: int


class TransferOwnershipRequest(BaseModel):
    new_owner_membership_id: uuid.UUID

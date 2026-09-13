import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ActivityLogRead(BaseModel):
    id: uuid.UUID
    clinic_id: uuid.UUID | None
    actor_user_id: uuid.UUID | None
    actor_name: str | None = None
    actor_type: str
    action: str
    target_type: str | None
    target_id: str | None
    summary: str
    metadata: dict[str, Any] | None = Field(default=None, validation_alias="metadata_")
    created_at: datetime

    model_config = {"from_attributes": True, "populate_by_name": True}


class ActivityLogListResponse(BaseModel):
    items: list[ActivityLogRead]
    total: int
    page: int
    page_size: int

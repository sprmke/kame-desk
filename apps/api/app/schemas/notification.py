import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class NotificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    clinic_id: uuid.UUID
    type: str
    title: str
    body: str | None
    entity_type: str | None
    entity_id: str | None
    href: str | None
    metadata: dict = Field(validation_alias="metadata_")
    actor_user_id: uuid.UUID | None
    created_at: datetime
    is_read: bool = False


class NotificationListResponse(BaseModel):
    items: list[NotificationRead]
    total: int
    page: int
    page_size: int
    unread_count: int
    unread_capped: bool = False


class MarkAllReadRequest(BaseModel):
    pass


class NotificationPrefsRead(BaseModel):
    prefs: dict[str, dict[str, bool]]


class NotificationPrefsUpdate(BaseModel):
    prefs: dict[str, dict[str, bool]]


class PushSubscriptionCreate(BaseModel):
    endpoint: str
    keys: dict[str, str]


class PushSubscriptionRead(BaseModel):
    id: uuid.UUID
    endpoint: str

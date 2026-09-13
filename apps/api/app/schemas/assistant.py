import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.ai.assistant.context import AttachedContextItem, PageContext


class AssistantConversationRead(BaseModel):
    id: uuid.UUID
    clinic_id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AssistantMessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=8000)
    page_context: PageContext | None = None
    attached_context: list[AttachedContextItem] = Field(default_factory=list)


class AssistantActionRead(BaseModel):
    action_id: uuid.UUID
    status: str
    result: dict | None = None

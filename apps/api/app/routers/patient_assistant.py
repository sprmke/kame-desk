import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.patient_assistant.service import stream_patient_assistant_turn
from app.core.db import get_db

router = APIRouter(prefix="/public/clinics", tags=["public-assistant"])


class PatientAssistantMessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=4000)
    conversation_id: uuid.UUID | None = None


@router.post("/{slug}/assistant/messages")
async def post_patient_assistant_message(
    slug: str,
    data: PatientAssistantMessageCreate,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> StreamingResponse:
    return StreamingResponse(
        stream_patient_assistant_turn(
            db,
            slug,
            request,
            data.content,
            data.conversation_id,
        ),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )

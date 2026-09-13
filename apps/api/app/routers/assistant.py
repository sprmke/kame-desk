import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.assistant.service import (
    cancel_action,
    confirm_action,
    create_conversation,
    stream_assistant_turn,
)
from app.core.db import get_db
from app.core.deps import ClinicStaff, OwnerOnly
from app.core.security import get_active_clinic_membership, get_current_user
from app.models import ClinicMembership, User
from app.schemas.assistant import AssistantConversationRead, AssistantMessageCreate
from app.services.ai_usage_service import list_ai_usage

router = APIRouter(prefix="/assistant", tags=["assistant"])


async def _clinic_id(
    membership: Annotated[ClinicMembership, Depends(get_active_clinic_membership)],
) -> uuid.UUID:
    return membership.clinic_id


@router.get("/usage")
async def get_usage(
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    membership: OwnerOnly,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    return await list_ai_usage(db, clinic_id)


@router.post("/conversations", response_model=AssistantConversationRead)
async def post_conversation(
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    membership: ClinicStaff,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AssistantConversationRead:
    row = await create_conversation(db, clinic_id, user)
    return AssistantConversationRead.model_validate(row)


@router.post("/conversations/{conversation_id}/messages")
async def post_message(
    conversation_id: uuid.UUID,
    data: AssistantMessageCreate,
    membership: ClinicStaff,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> StreamingResponse:
    return StreamingResponse(
        stream_assistant_turn(db, conversation_id, data, membership, user),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/actions/{action_id}/confirm")
async def post_confirm_action(
    action_id: uuid.UUID,
    membership: ClinicStaff,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    return await confirm_action(db, action_id, membership, user)


@router.post("/actions/{action_id}/cancel")
async def post_cancel_action(
    action_id: uuid.UUID,
    membership: ClinicStaff,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    return await cancel_action(db, action_id, membership, user)

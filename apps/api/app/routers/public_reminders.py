from typing import Annotated, Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.services.reminder_service import respond_to_reminder

router = APIRouter(tags=["public-reminders"])


class ReminderRespond(BaseModel):
    action: Literal["confirm", "cancel", "reschedule_request"]
    message: str | None = Field(default=None, max_length=500)


@router.post("/public/reminders/{token}/respond")
async def post_reminder_respond(
    token: str,
    data: ReminderRespond,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, str]:
    status = await respond_to_reminder(db, token, data.action, data.message)
    return {"status": status}

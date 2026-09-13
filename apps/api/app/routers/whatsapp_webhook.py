import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_db
from app.models import Clinic
from app.services.reminder_service import respond_to_reminder
from app.services.whatsapp_service import parse_whatsapp_inbound

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks/whatsapp", tags=["whatsapp-webhook"])


@router.get("")
async def verify_webhook(
    hub_mode: Annotated[str | None, Query(alias="hub.mode")] = None,
    hub_verify_token: Annotated[str | None, Query(alias="hub.verify_token")] = None,
    hub_challenge: Annotated[str | None, Query(alias="hub.challenge")] = None,
) -> Response:
    if hub_mode == "subscribe" and hub_verify_token == settings.whatsapp_webhook_verify_token:
        return Response(content=hub_challenge or "", media_type="text/plain")
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("")
async def receive_webhook(
    payload: dict[str, Any],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, str]:
    parsed = parse_whatsapp_inbound(payload)
    if parsed is None:
        # Delivery-status callbacks and unrecognized payloads are expected
        # traffic on this webhook — always 200 so Meta doesn't retry/disable it.
        return {"status": "ignored"}

    result = await db.execute(
        select(Clinic).where(Clinic.whatsapp_phone_number_id == parsed["phone_number_id"])
    )
    clinic = result.scalars().first()
    if clinic is None:
        logger.warning("WhatsApp webhook: no clinic matches inbound phone_number_id")
        return {"status": "ignored"}

    reply_token = parsed.get("reply_token")
    if not reply_token:
        text = (parsed.get("text") or "").strip()
        if text:
            from app.services.notification_service import notify_messaging_inbound

            sender = parsed.get("from") or "unknown"
            await notify_messaging_inbound(
                db,
                clinic_id=clinic.id,
                conversation_key=sender,
                preview=text,
            )
        return {"status": "ignored"}

    text = (parsed.get("text") or "").strip().lower()
    action = "cancel" if "cancel" in text else "confirm"
    try:
        status = await respond_to_reminder(db, reply_token, action)
    except HTTPException:
        return {"status": "ignored"}
    return {"status": status}

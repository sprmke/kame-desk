from __future__ import annotations

from typing import Any

from app.services.messaging.base import OutboundMessage
from app.services.whatsapp_service import parse_whatsapp_inbound, send_whatsapp_template


class WhatsAppChannel:
    name = "whatsapp"

    async def send(self, message: OutboundMessage) -> str:
        if not message.to or not message.creds:
            raise ValueError("WhatsApp requires a recipient phone number and Business credentials")
        return await send_whatsapp_template(
            to=message.to,
            reminder_type=message.reminder_type,
            body_param=message.body,
            reply_token=message.reply_token,
            creds=message.creds,
        )

    def parse_inbound_reply(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        parsed = parse_whatsapp_inbound(payload)
        if parsed is None or not parsed.get("reply_token"):
            return None
        text = (parsed.get("text") or "").strip().lower()
        action = "cancel" if "cancel" in text else "confirm"
        return {"reply_token": parsed["reply_token"], "action": action}

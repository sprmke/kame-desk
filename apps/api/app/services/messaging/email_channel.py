from __future__ import annotations

from typing import Any

from app.services.email_service import send_reminder_email
from app.services.messaging.base import OutboundMessage


class EmailChannel:
    name = "email"

    async def send(self, message: OutboundMessage) -> str:
        if not message.to:
            raise ValueError("Email requires a recipient address")
        return send_reminder_email(message.to, message.subject, message.body, message.sender_name)

    def parse_inbound_reply(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        # Email replies aren't parsed — patients use the reply_token link
        # embedded in the message body (see public_reminders router).
        return None

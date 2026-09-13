from __future__ import annotations

from typing import Any

from app.services.messaging.base import OutboundMessage
from app.services.sms_service import send_twilio_sms


class SmsChannel:
    name = "sms"

    async def send(self, message: OutboundMessage) -> str:
        if not message.to or not message.creds:
            raise ValueError("SMS requires a recipient phone number and Twilio credentials")
        return await send_twilio_sms(to=message.to, body=message.body, creds=message.creds)

    def parse_inbound_reply(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        # No inbound SMS webhook is wired yet — patients use the reply_token
        # link embedded in the message body, same as email.
        return None

from __future__ import annotations

from app.services.messaging.base import MessageChannel
from app.services.messaging.email_channel import EmailChannel
from app.services.messaging.sms_channel import SmsChannel
from app.services.messaging.stubs import MessengerChannel, ViberChannel
from app.services.messaging.whatsapp_channel import WhatsAppChannel

CHANNELS: dict[str, MessageChannel] = {
    "email": EmailChannel(),
    "sms": SmsChannel(),
    "whatsapp": WhatsAppChannel(),
    "messenger": MessengerChannel(),
    "viber": ViberChannel(),
}


def get_channel(name: str) -> MessageChannel:
    channel = CHANNELS.get(name)
    if channel is None:
        raise ValueError(f"Unknown messaging channel: {name}")
    return channel

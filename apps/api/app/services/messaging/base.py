from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass
class OutboundMessage:
    """Everything a channel adapter might need to send one reminder."""

    to: str | None
    subject: str
    body: str
    reminder_type: str
    reply_token: str
    creds: dict[str, Any] | None = None
    sender_name: str | None = None


class MessageChannel(Protocol):
    """Adapter interface every messaging channel implements.

    `send` delivers one outbound message and returns a provider message id.
    `parse_inbound_reply` turns a provider webhook payload into
    `{"reply_token": str, "action": "confirm" | "cancel"} | None` (None when
    the payload doesn't map to a recognized reply), or raises
    NotImplementedError for channels with no inbound webhook wired yet.
    """

    name: str

    async def send(self, message: OutboundMessage) -> str: ...

    def parse_inbound_reply(self, payload: dict[str, Any]) -> dict[str, Any] | None: ...

from __future__ import annotations

from typing import Any

from app.services.messaging.base import OutboundMessage


class MessengerChannel:
    """Documented stub. Satisfies the MessageChannel interface so a future
    phase can activate Messenger without a data-model change, but is not
    wired to a live API — per the market-research plan's recommendation to
    validate WhatsApp with real pilot clinics before building all three
    channels (see phase-35 Production defaults)."""

    name = "messenger"

    async def send(self, message: OutboundMessage) -> str:
        raise NotImplementedError("Messenger channel is not wired to a live API yet")

    def parse_inbound_reply(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        raise NotImplementedError("Messenger channel is not wired to a live API yet")


class ViberChannel:
    """Documented stub — see MessengerChannel."""

    name = "viber"

    async def send(self, message: OutboundMessage) -> str:
        raise NotImplementedError("Viber channel is not wired to a live API yet")

    def parse_inbound_reply(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        raise NotImplementedError("Viber channel is not wired to a live API yet")

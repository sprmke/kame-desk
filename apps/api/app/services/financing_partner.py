"""Pluggable patient-financing/BNPL submission partner.

No confirmed Philippine healthcare-specific BNPL partner exists yet (see
docs/phases/phase-38-growth-retention-features.md). MVP ships only the no-op
adapter behind `settings.financing_partner_enabled` — the invoice-side hook
(status field + action) is real, but nothing is actually submitted anywhere
until a real provider is integrated behind this same protocol.
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Protocol


class FinancingPartner(Protocol):
    async def create_financing_request(
        self, *, invoice_id: uuid.UUID, amount: Decimal, patient_name: str
    ) -> str | None:
        """Submit a financing request. Returns a partner reference, if any."""
        ...


class NoopFinancingPartner:
    """Default adapter: tracks the request in-app only, submits nowhere."""

    async def create_financing_request(
        self, *, invoice_id: uuid.UUID, amount: Decimal, patient_name: str
    ) -> str | None:
        return None


def get_financing_partner() -> FinancingPartner:
    return NoopFinancingPartner()

"""Pluggable claims/eligibility/LOA submission partner.

MVP ships only the manual adapter: kame-desk does not pursue its own PhilHealth
HITP / BIR CAS certification (see docs/phases/phase-33-ph-payer-workflow.md).
Staff enter reference numbers and decisions by hand; a real HITP API adapter
can be added later behind this same protocol without changing callers.
"""

from __future__ import annotations

from typing import Protocol


class ClaimsPartner(Protocol):
    async def submit_eligibility_check(self, *, payer_name: str, member_id: str | None) -> None:
        """Notify the partner an eligibility check was requested. No-op for the manual adapter."""
        ...

    async def submit_loa_request(self, *, hmo_name: str, reference_number: str | None) -> None:
        """Notify the partner an LOA request was submitted. No-op for the manual adapter."""
        ...

    async def submit_claim(self, *, provider: str, claim_reference: str | None) -> None:
        """Notify the partner a claim was submitted. No-op for the manual adapter."""
        ...


class ManualClaimsPartner:
    """Default adapter: every submission is tracked in-app and actioned by clinic staff."""

    async def submit_eligibility_check(self, *, payer_name: str, member_id: str | None) -> None:
        return None

    async def submit_loa_request(self, *, hmo_name: str, reference_number: str | None) -> None:
        return None

    async def submit_claim(self, *, provider: str, claim_reference: str | None) -> None:
        return None


def get_claims_partner() -> ClaimsPartner:
    return ManualClaimsPartner()

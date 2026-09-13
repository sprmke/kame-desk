import logging
import re
import uuid
from typing import Any

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models import Clinic, ClinicMembership
from app.services.clinic_service import get_clinic

logger = logging.getLogger(__name__)

NEVER_BUILD_TOOL_NAMES = frozenset(
    {
        "delete_patient",
        "delete_chart_version",
        "bulk_message_patients",
        "execute_sql",
        "disable_rbac",
    }
)


def assert_assistant_enabled(clinic: Clinic) -> None:
    if not settings.platform_ai_assistant_enabled:
        raise HTTPException(status_code=503, detail="AI assistant unavailable")
    if not clinic.ai_assistant_enabled:
        raise HTTPException(status_code=403, detail="AI assistant disabled for this clinic")


async def load_clinic_for_assistant(db: AsyncSession, clinic_id: uuid.UUID) -> Clinic:
    from app.models.platform import PlatformFeatureFlag

    clinic = await get_clinic(db, clinic_id)
    flag = await db.get(PlatformFeatureFlag, "ai_assistant")
    if flag is not None:
        if not flag.enabled:
            raise HTTPException(status_code=503, detail="AI assistant unavailable")
    elif not settings.platform_ai_assistant_enabled:
        raise HTTPException(status_code=503, detail="AI assistant unavailable")
    if not clinic.ai_assistant_enabled:
        raise HTTPException(status_code=403, detail="AI assistant disabled for this clinic")
    return clinic


def assert_tool_registered(tool_name: str) -> None:
    if tool_name in NEVER_BUILD_TOOL_NAMES:
        raise HTTPException(status_code=400, detail="Tool not available")


def assert_tool_role(membership: ClinicMembership, allowed_roles: tuple[str, ...]) -> None:
    if membership.role not in allowed_roles:
        raise HTTPException(status_code=403, detail="Permission denied for this action")


def log_tool_call(tool_name: str, tier: int, outcome: str) -> None:
    logger.info(
        "ai_assistant_tool",
        extra={"tool": tool_name, "tier": tier, "outcome": outcome},
    )


def ground_assistant_text(text: str, grounded_facts: list[str]) -> str:
    """Drop sentences that cite facts not present in tool results."""
    if not grounded_facts:
        return text
    blob = " ".join(grounded_facts).lower()
    kept: list[str] = []
    for sentence in re.split(r"(?<=[.!?])\s+", text.strip()):
        if not sentence:
            continue
        tokens = re.findall(r"\b[\w$.,]+\b", sentence.lower())
        if not tokens:
            kept.append(sentence)
            continue
        if any(tok in blob for tok in tokens if len(tok) > 3):
            kept.append(sentence)
    return " ".join(kept) if kept else "Done."


def collect_grounding_strings(payload: Any) -> list[str]:
    if payload is None:
        return []
    if isinstance(payload, str):
        return [payload]
    if isinstance(payload, (int, float, bool)):
        return [str(payload)]
    if isinstance(payload, dict):
        out: list[str] = []
        for value in payload.values():
            out.extend(collect_grounding_strings(value))
        return out
    if isinstance(payload, list):
        out: list[str] = []
        for item in payload:
            out.extend(collect_grounding_strings(item))
        return out
    return [str(payload)]

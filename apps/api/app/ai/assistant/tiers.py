from dataclasses import dataclass

from app.ai.assistant.context import ResolvedContext, is_cross_scope

EXTERNAL_SEND_TOOL_NAMES = frozenset({"propose_send_reminder"})


@dataclass
class PlannedToolCall:
    name: str
    args: dict
    base_tier: int
    is_write: bool
    is_clinical_write: bool = False
    is_external_send: bool = False


def classify_tier(
    call: PlannedToolCall,
    all_calls: list[PlannedToolCall],
    ctx: ResolvedContext,
) -> int:
    tier = call.base_tier

    if call.is_clinical_write:
        tier = max(tier, 2)
    if call.is_external_send or call.name in EXTERNAL_SEND_TOOL_NAMES:
        tier = max(tier, 2)

    write_count = sum(1 for c in all_calls if c.is_write)
    if write_count >= 2:
        tier = max(tier, 2)

    if is_cross_scope(call.args, ctx):
        tier = max(tier, 2)

    if call.name in ("propose_book_appointment", "propose_reschedule_appointment"):
        start = str(call.args.get("scheduled_start") or "")
        hour = _hour_from_iso(start)
        if hour is not None and (hour < 8 or hour >= 18):
            tier = max(tier, 2)
        if call.args.get("overlap_risk"):
            tier = max(tier, 2)

    return tier


def _hour_from_iso(value: str) -> int | None:
    if "T" not in value:
        return None
    try:
        from datetime import datetime
        from zoneinfo import ZoneInfo

        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            return parsed.hour
        return parsed.astimezone(ZoneInfo("Asia/Manila")).hour
    except (ValueError, IndexError):
        return None

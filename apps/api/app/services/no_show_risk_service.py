"""Explainable no-show risk heuristic (additive to Phase 11 reminders)."""

from datetime import UTC, datetime
from typing import Any

from app.models import Appointment, Patient


def compute_no_show_risk(appt: Appointment, patient: Patient | None) -> dict[str, Any]:
    if appt.appointment_status in ("Cancelled", "No Show", "Rescheduled"):
        return {"level": "none", "score": 0, "reasons": []}

    score = 0
    reasons: list[str] = []
    start = appt.scheduled_start
    if start.tzinfo is None:
        start = start.replace(tzinfo=UTC)
    now = datetime.now(UTC)
    lead_hours = max(0.0, (start - now).total_seconds() / 3600.0)
    if lead_hours < 24:
        score += 2
        reasons.append("Booked within 24 hours")
    elif lead_hours < 72:
        score += 1
        reasons.append("Booked within 3 days")

    weekday = start.weekday()
    if weekday in (0, 6):
        score += 1
        reasons.append("Weekend or Monday slot")

    past_no_shows = patient.no_show_count if patient else 0
    if past_no_shows >= 2:
        score += 3
        reasons.append("Two or more past no-shows")
    elif past_no_shows == 1:
        score += 1
        reasons.append("One past no-show")

    level = "high" if score >= 3 else "low" if score >= 1 else "none"
    return {"level": level, "score": score, "reasons": reasons}

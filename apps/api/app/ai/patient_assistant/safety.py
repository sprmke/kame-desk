"""Output safety for patient-facing assistant responses."""

import re
from typing import Any

CONTACT_FALLBACK = "Please contact the clinic directly for that question."

HMO_PATTERNS = (
    r"\bwe accept\b.*\bhmo\b",
    r"\byes[, ]+ we (take|accept)\b",
    r"\ball (major )?hmos\b",
)


def verify_output_safety(text: str, grounding: dict[str, Any]) -> str:
    lowered = text.lower()
    if grounding.get("accepts_hmo") is not True:
        for pattern in HMO_PATTERNS:
            if re.search(pattern, lowered):
                return CONTACT_FALLBACK

    for name in grounding.get("_forbidden_names", []):
        if name and name.lower() in lowered:
            return CONTACT_FALLBACK

    return text.strip()

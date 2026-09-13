"""Heuristic billing document field extraction from plain text."""

import re
from typing import Any

FieldResult = dict[str, Any]


def _field(value: str | None, confidence: str) -> FieldResult:
    return {"value": value, "confidence": confidence}


def extract_billing_fields_from_text(text: str) -> dict[str, FieldResult]:
    cleaned = text.strip()
    if not cleaned:
        return {
            "amount": _field(None, "missing"),
            "date": _field(None, "missing"),
            "provider": _field(None, "missing"),
            "reference_number": _field(None, "missing"),
        }

    amount: str | None = None
    amount_conf = "missing"
    amount_patterns = [
        r"(?:PHP|₱|P)\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{2})?)",
        r"(?:total|amount|paid)\s*[:\-]?\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{2})?)",
    ]
    for pattern in amount_patterns:
        match = re.search(pattern, cleaned, re.IGNORECASE)
        if match:
            amount = match.group(1).replace(",", "")
            amount_conf = "high" if "total" in match.group(0).lower() else "low"
            break

    extracted_date: str | None = None
    date_conf = "missing"
    date_match = re.search(r"\b(20\d{2}-\d{2}-\d{2})\b", cleaned)
    if date_match:
        extracted_date = date_match.group(1)
        date_conf = "high"
    else:
        slash = re.search(r"\b(\d{1,2}/\d{1,2}/20\d{2})\b", cleaned)
        if slash:
            extracted_date = slash.group(1)
            date_conf = "low"

    provider: str | None = None
    provider_conf = "missing"
    provider_match = re.search(
        r"(?:provider|clinic|hospital|merchant)\s*[:\-]\s*([A-Za-z0-9 .,&'-]{3,80})",
        cleaned,
        re.IGNORECASE,
    )
    if provider_match:
        provider = provider_match.group(1).strip()
        provider_conf = "high"

    reference: str | None = None
    ref_conf = "missing"
    ref_match = re.search(
        r"(?:ref(?:erence)?|or|invoice|receipt)\s*(?:no\.?|#)?\s*[:\-]?\s*([A-Z0-9\-]{4,32})",
        cleaned,
        re.IGNORECASE,
    )
    if ref_match:
        reference = ref_match.group(1).strip()
        ref_conf = "high"

    if len(cleaned) < 40 and amount is None:
        amount_conf = "missing"
        date_conf = "missing"

    return {
        "amount": _field(amount, amount_conf),
        "date": _field(extracted_date, date_conf),
        "provider": _field(provider, provider_conf),
        "reference_number": _field(reference, ref_conf),
    }


def fixture_receipt_text() -> str:
    return (
        "St. Luke's Medical Center\n"
        "Receipt No: OR-2026-00421\n"
        "Date: 2026-09-01\n"
        "Total: PHP 1,250.00\n"
    )

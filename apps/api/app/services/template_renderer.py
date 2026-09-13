"""Sandboxed {{placeholder}} rendering for clinic document templates."""

import re
from typing import Any

PLACEHOLDER_PATTERN = re.compile(r"\{\{([a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)*)\}\}")
FORBIDDEN_SUBSTRINGS = ("{%", "%}", "${", "__")
# Word-bounded so normal clinical prose ("evaluation", "keep the wound open")
# doesn't false-positive on substrings like "eval" or "open".
FORBIDDEN_WORD_PATTERN = re.compile(r"\b(?:import|eval|exec)\b|\bopen\(")


def validate_template_body(body: str) -> None:
    if any(token in body for token in FORBIDDEN_SUBSTRINGS):
        raise ValueError("Template contains forbidden syntax")
    if FORBIDDEN_WORD_PATTERN.search(body):
        raise ValueError("Template contains forbidden syntax")
    for match in PLACEHOLDER_PATTERN.finditer(body):
        key = match.group(1)
        if key.count(".") > 2:
            raise ValueError(f"Invalid placeholder depth: {key}")


def flatten_context(data: dict[str, Any], prefix: str = "") -> dict[str, str]:
    flat: dict[str, str] = {}
    for key, value in data.items():
        path = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            flat.update(flatten_context(value, path))
        elif value is None:
            flat[path] = ""
        else:
            flat[path] = str(value)
    return flat


def render_template(body: str, context: dict[str, Any]) -> str:
    validate_template_body(body)
    flat = flatten_context(context)

    def replace(match: re.Match[str]) -> str:
        key = LEGACY_PLACEHOLDER_ALIASES.get(match.group(1), match.group(1))
        return flat.get(key, "")

    return PLACEHOLDER_PATTERN.sub(replace, body)


TEMPLATE_PLACEHOLDERS = (
    "patient.full_name",
    "patient.birthdate",
    "patient.contact_number",
    "patient.address",
    "clinic.name",
    "clinic.address",
    "clinic.contact_phone",
    "doctor.full_name",
    "doctor.specialty",
    "doctor.prc_license_number",
    "visit.date",
    "visit.reason_for_visit",
)

# Older seed templates used undotted keys. Still fill them at render time.
LEGACY_PLACEHOLDER_ALIASES = {
    "patient_name": "patient.full_name",
    "visit_date": "visit.date",
}

SAMPLE_TEMPLATE_CONTEXT = {
    "patient": {
        "full_name": "Maria Santos",
        "birthdate": "1988-03-12",
        "contact_number": "+639171000000",
        "address": "Makati",
    },
    "clinic": {
        "name": "Sample Clinic",
        "address": "123 Clinic St",
        "contact_phone": "+63281234567",
    },
    "doctor": {
        "full_name": "Dr Santos",
        "specialty": "General Practice",
        "prc_license_number": "PRC-0000",
    },
    "visit": {
        "reason_for_visit": "Follow-up",
        "date": "2026-09-11",
    },
}

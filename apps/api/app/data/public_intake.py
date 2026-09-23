"""Public booking intake field keys. Name and phone are always required."""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException

INTAKE_KEYS = (
    "email",
    "birthdate",
    "sex",
    "address",
    "reason",
    "existing_patient",
    "notes",
)

DEFAULT_INTAKE_FIELDS: dict[str, bool] = {key: False for key in INTAKE_KEYS}


def normalize_intake_fields(raw: Any) -> dict[str, bool]:
    fields = dict(DEFAULT_INTAKE_FIELDS)
    if isinstance(raw, dict):
        for key in INTAKE_KEYS:
            if key in raw:
                fields[key] = bool(raw[key])
    return fields


def require_public_intake(fields: dict[str, bool], data: Any) -> None:
    checks: list[tuple[str, bool, str]] = [
        ("email", fields["email"], "Email is required"),
        ("birthdate", fields["birthdate"], "Birthdate is required"),
        ("sex", fields["sex"], "Sex is required"),
        ("address", fields["address"], "Address is required"),
        ("reason_for_visit", fields["reason"], "Reason is required"),
        ("is_existing_patient", fields["existing_patient"], "Select new or existing"),
    ]
    for attr, required, message in checks:
        if required and getattr(data, attr, None) in (None, ""):
            raise HTTPException(status_code=400, detail=message)

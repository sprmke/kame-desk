"""Doctor specialty catalog (profile keys). Separate from SOAP templates."""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import HTTPException


@dataclass(frozen=True)
class DoctorSpecialty:
    key: str
    label: str
    soap_template_key: str


SPECIALTY_CATALOG: tuple[DoctorSpecialty, ...] = (
    DoctorSpecialty("dentist", "Dentist", "dental"),
    DoctorSpecialty("obgyn", "OB-GYN", "obgyn"),
    DoctorSpecialty("pediatrician", "Pediatrician", "pediatric"),
    DoctorSpecialty("general_practitioner", "General practitioner", "general"),
    DoctorSpecialty("dermatologist", "Dermatologist", "dermatology"),
    DoctorSpecialty("cardiologist", "Cardiologist", "general"),
    DoctorSpecialty("ophthalmologist", "Ophthalmologist", "general"),
    DoctorSpecialty("orthopedic", "Orthopedic", "general"),
    DoctorSpecialty("ent", "ENT", "general"),
    DoctorSpecialty("other", "Other", "general"),
)

SPECIALTY_BY_KEY = {item.key: item for item in SPECIALTY_CATALOG}

# Lowercased free-text values seen in seed/tests/legacy rows.
LEGACY_SPECIALTY_MAP: dict[str, str] = {
    "dentist": "dentist",
    "dental": "dentist",
    "dentistry": "dentist",
    "ob-gyn": "obgyn",
    "obgyn": "obgyn",
    "ob/gyn": "obgyn",
    "obstetrics": "obgyn",
    "pediatrician": "pediatrician",
    "pediatrics": "pediatrician",
    "pedia": "pediatrician",
    "general practitioner": "general_practitioner",
    "general practice": "general_practitioner",
    "family medicine": "general_practitioner",
    "gp": "general_practitioner",
    "dermatologist": "dermatologist",
    "dermatology": "dermatologist",
    "cardiologist": "cardiologist",
    "cardiology": "cardiologist",
    "ophthalmologist": "ophthalmologist",
    "ophthalmology": "ophthalmologist",
    "orthopedic": "orthopedic",
    "orthopaedics": "orthopedic",
    "ent": "ent",
    "otolaryngology": "ent",
}


def catalog_as_dicts() -> list[dict[str, str]]:
    return [
        {
            "key": item.key,
            "label": item.label,
            "soap_template_key": item.soap_template_key,
        }
        for item in SPECIALTY_CATALOG
    ]


def soap_template_for_specialty_key(key: str | None) -> str:
    if not key:
        return "general"
    item = SPECIALTY_BY_KEY.get(key)
    return item.soap_template_key if item else "general"


def resolve_specialty(
    *,
    specialty_key: str | None = None,
    specialty_other: str | None = None,
    specialty: str | None = None,
) -> tuple[str, str | None, str]:
    """Return (key, other_text, display_label)."""
    key = (specialty_key or "").strip()
    other = (specialty_other or "").strip() or None
    legacy = (specialty or "").strip() or None

    if key:
        item = SPECIALTY_BY_KEY.get(key)
        if item is None:
            raise HTTPException(status_code=400, detail="Unknown specialty")
        if item.key == "other":
            if not other and not legacy:
                raise HTTPException(status_code=400, detail="Enter a specialty")
            other = other or legacy
            return item.key, other, other
        return item.key, None, item.label

    if legacy:
        mapped = LEGACY_SPECIALTY_MAP.get(legacy.lower())
        if mapped and mapped != "other":
            item = SPECIALTY_BY_KEY[mapped]
            return item.key, None, item.label
        return "other", legacy, legacy

    raise HTTPException(status_code=400, detail="Specialty is required")

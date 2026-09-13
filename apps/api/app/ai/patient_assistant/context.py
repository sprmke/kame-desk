"""Guest-safe grounding facts for the public booking assistant."""

from typing import Any

from app.models import Clinic, DoctorProfile, ServiceFee, User

FORBIDDEN_GROUNDING_KEYS = frozenset(
    {
        "patient_id",
        "patient_name",
        "full_name",
        "contact_number",
        "email",
        "reason_for_visit",
        "soap",
        "diagnosis",
        "allergies",
    }
)


def build_grounding_facts(
    clinic: Clinic,
    doctors: list[tuple[DoctorProfile, User]],
    fees: list[ServiceFee],
) -> dict[str, Any]:
    facts: dict[str, Any] = {
        "clinic_name": clinic.name,
        "slug": clinic.slug,
        "address": clinic.address,
        "contact_phone": clinic.contact_phone,
        "contact_email": clinic.contact_email,
        "working_hours": clinic.working_hours,
        "holiday_dates": clinic.holiday_dates or [],
        "default_appointment_duration_minutes": clinic.default_appointment_duration_minutes,
        "doctors": [
            {
                "id": str(d.id),
                "full_name": u.full_name,
                "specialty": d.specialty,
            }
            for d, u in doctors
        ],
        "services": [{"name": f.name, "amount": str(f.amount)} for f in fees],
        "accepts_hmo": False,
    }
    return sanitize_grounding_facts(facts)


def sanitize_grounding_facts(payload: dict[str, Any]) -> dict[str, Any]:
    def walk(value: Any) -> Any:
        if isinstance(value, dict):
            return {
                key: walk(inner)
                for key, inner in value.items()
                if key not in FORBIDDEN_GROUNDING_KEYS
            }
        if isinstance(value, list):
            return [walk(item) for item in value]
        return value

    return walk(payload)

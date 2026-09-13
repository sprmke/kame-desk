"""Minimal, read-only, on-demand FHIR R4 export.

Not a live PHIE (Philippine Health Information Exchange) connection — no PHIE
sandbox/credentials exist to integrate against (see
docs/phases/phase-38-growth-retention-features.md). This produces a
self-contained FHIR R4 Bundle (Patient + Encounter resources) for a single
patient, useful for one-off interoperability requests.
"""

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Appointment, Patient

_SEX_TO_FHIR_GENDER = {"male": "male", "female": "female"}


def _patient_resource(patient: Patient) -> dict[str, Any]:
    parts = patient.full_name.strip().rsplit(" ", 1)
    given, family = (parts[0], parts[1]) if len(parts) == 2 else (patient.full_name, "")
    telecom = []
    if patient.contact_number:
        telecom.append({"system": "phone", "value": patient.contact_number})
    if patient.email:
        telecom.append({"system": "email", "value": patient.email})
    resource: dict[str, Any] = {
        "resourceType": "Patient",
        "id": str(patient.id),
        "name": [{"family": family, "given": [given]}],
    }
    if patient.birthdate:
        resource["birthDate"] = patient.birthdate.isoformat()
    if patient.sex and patient.sex.lower() in _SEX_TO_FHIR_GENDER:
        resource["gender"] = _SEX_TO_FHIR_GENDER[patient.sex.lower()]
    if telecom:
        resource["telecom"] = telecom
    if patient.address:
        resource["address"] = [{"text": patient.address}]
    return resource


def _encounter_resource(appt: Appointment, patient_id: uuid.UUID) -> dict[str, Any]:
    resource: dict[str, Any] = {
        "resourceType": "Encounter",
        "id": str(appt.id),
        "status": "finished" if appt.current_visit_status == "Completed" else "unknown",
        "class": {
            "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
            "code": "AMB",
            "display": "ambulatory",
        },
        "subject": {"reference": f"Patient/{patient_id}"},
        "period": {
            "start": appt.scheduled_start.isoformat(),
            "end": appt.scheduled_end.isoformat(),
        },
    }
    if appt.reason_for_visit:
        resource["reasonCode"] = [{"text": appt.reason_for_visit}]
    return resource


async def build_patient_fhir_bundle(
    db: AsyncSession, clinic_id: uuid.UUID, patient: Patient
) -> dict[str, Any]:
    result = await db.execute(
        select(Appointment)
        .where(Appointment.patient_id == patient.id, Appointment.clinic_id == clinic_id)
        .order_by(Appointment.scheduled_start.desc())
    )
    appointments = list(result.scalars().all())

    entries = [{"resource": _patient_resource(patient)}]
    entries.extend({"resource": _encounter_resource(a, patient.id)} for a in appointments)

    return {
        "resourceType": "Bundle",
        "type": "collection",
        "entry": entries,
    }

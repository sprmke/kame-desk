import csv
import io
import uuid
from datetime import date

from fastapi import HTTPException
from sqlalchemy import or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    ActivityLog,
    Appointment,
    AppointmentSeries,
    BillingExtractionAttempt,
    GeneratedDocument,
    Invoice,
    Patient,
    PatientFile,
    PatientMedicalInfo,
    PatientRecall,
    PatientVital,
    Prescription,
    Reminder,
    SoapNote,
)
from app.schemas.patient import PatientCreate, PatientRead
from app.services.patient_service import create_patient, get_patient


async def find_possible_matches(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    *,
    full_name: str | None,
    contact_number: str | None,
    exclude_id: uuid.UUID | None = None,
) -> list[Patient]:
    filters = [Patient.clinic_id == clinic_id, Patient.is_archived.is_(False)]
    if exclude_id:
        filters.append(Patient.id != exclude_id)
    clauses = []
    if full_name and full_name.strip():
        clauses.append(Patient.full_name.ilike(full_name.strip()))
    if contact_number and contact_number.strip():
        clauses.append(Patient.contact_number == contact_number.strip())
    if not clauses:
        return []
    result = await db.execute(select(Patient).where(*filters, or_(*clauses)).limit(10))
    return list(result.scalars().all())


def _merge_lists(left: list, right: list) -> list:
    out = list(left or [])
    for item in right or []:
        if item not in out:
            out.append(item)
    return out


async def merge_patients(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    target_id: uuid.UUID,
    source_id: uuid.UUID,
    actor_id: uuid.UUID,
) -> Patient:
    if target_id == source_id:
        raise HTTPException(status_code=400, detail="Cannot merge a patient into itself")
    target = await get_patient(db, clinic_id, target_id)
    source = await get_patient(db, clinic_id, source_id)
    if source.is_archived:
        raise HTTPException(status_code=400, detail="Source patient is already archived")

    reassign = (
        Appointment,
        AppointmentSeries,
        Invoice,
        Prescription,
        GeneratedDocument,
        PatientFile,
        PatientVital,
        Reminder,
        SoapNote,
        BillingExtractionAttempt,
    )
    for model in reassign:
        await db.execute(
            update(model)
            .where(model.clinic_id == clinic_id, model.patient_id == source.id)
            .values(patient_id=target.id)
        )

    source_recalls = await db.execute(
        select(PatientRecall).where(
            PatientRecall.clinic_id == clinic_id, PatientRecall.patient_id == source.id
        )
    )
    for recall in source_recalls.scalars():
        clash = await db.execute(
            select(PatientRecall).where(
                PatientRecall.clinic_id == clinic_id,
                PatientRecall.patient_id == target.id,
                PatientRecall.source == recall.source,
                PatientRecall.due_date == recall.due_date,
            )
        )
        if clash.scalar_one_or_none():
            await db.delete(recall)
        else:
            recall.patient_id = target.id

    target_med = await db.execute(
        select(PatientMedicalInfo).where(PatientMedicalInfo.patient_id == target.id)
    )
    source_med = await db.execute(
        select(PatientMedicalInfo).where(PatientMedicalInfo.patient_id == source.id)
    )
    tmed = target_med.scalar_one_or_none()
    smed = source_med.scalar_one_or_none()
    if tmed and smed:
        tmed.allergies = _merge_lists(tmed.allergies, smed.allergies)
        tmed.current_medications = _merge_lists(tmed.current_medications, smed.current_medications)
        tmed.chronic_conditions = _merge_lists(tmed.chronic_conditions, smed.chronic_conditions)
        tmed.vaccination_history = _merge_lists(tmed.vaccination_history, smed.vaccination_history)
        if not tmed.medical_history and smed.medical_history:
            tmed.medical_history = smed.medical_history
        await db.delete(smed)

    if not target.insurance_info and source.insurance_info:
        target.insurance_info = source.insurance_info
    if not target.contact_number and source.contact_number:
        target.contact_number = source.contact_number
    source.is_archived = True

    db.add(
        ActivityLog(
            clinic_id=clinic_id,
            actor_user_id=actor_id,
            actor_type="user",
            action="patient.merged",
            target_type="patient",
            target_id=str(target.id),
            summary="Merged duplicate patient chart",
            metadata_={"source_patient_id": str(source.id)},
        )
    )
    await db.commit()
    await db.refresh(target)
    return target


async def import_patients_csv(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    csv_text: str,
    actor_id: uuid.UUID,
    *,
    commit: bool,
) -> dict:
    reader = csv.DictReader(io.StringIO(csv_text))
    required = {"full_name"}
    if not reader.fieldnames or not required.issubset({h.strip() for h in reader.fieldnames}):
        raise HTTPException(status_code=400, detail="CSV must include a full_name column")
    preview: list[dict] = []
    errors: list[str] = []
    created = 0
    for index, raw in enumerate(reader, start=2):
        name = (raw.get("full_name") or "").strip()
        if not name:
            errors.append(f"Row {index}: full_name is required")
            continue
        contact = (raw.get("contact_number") or "").strip() or None
        matches = await find_possible_matches(db, clinic_id, full_name=name, contact_number=contact)
        row = {
            "full_name": name,
            "birthdate": (raw.get("birthdate") or "").strip() or None,
            "contact_number": contact,
            "email": (raw.get("email") or "").strip() or None,
            "match_count": len(matches),
        }
        preview.append(row)
        if not commit:
            continue
        birthdate = None
        if row["birthdate"]:
            try:
                birthdate = date.fromisoformat(row["birthdate"])
            except ValueError:
                errors.append(f"Row {index}: invalid birthdate")
                continue
        await create_patient(
            db,
            clinic_id,
            PatientCreate(
                full_name=name,
                birthdate=birthdate,
                contact_number=contact,
                email=row["email"],
                data_processing_consent=True,
            ),
            actor_id,
        )
        created += 1
    if commit:
        db.add(
            ActivityLog(
                clinic_id=clinic_id,
                actor_user_id=actor_id,
                actor_type="user",
                action="patient.imported",
                target_type="clinic",
                target_id=str(clinic_id),
                summary="Imported patients from CSV",
                metadata_={"count": created},
            )
        )
        await db.commit()
    return {"items": preview, "errors": errors, "created": created, "committed": commit}


def patients_to_read(rows: list[Patient]) -> list[PatientRead]:
    return [PatientRead.model_validate(p) for p in rows]

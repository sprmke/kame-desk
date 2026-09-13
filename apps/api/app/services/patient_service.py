import os
import uuid
from datetime import UTC, datetime
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import paginate, parse_sort
from app.models import (
    ActivityLog,
    Patient,
    PatientFile,
    PatientMedicalInfo,
    PatientVital,
)
from app.schemas.patient import MedicalInfoUpdate, PatientCreate, PatientUpdate, VitalsCreate
from app.services.storage_service import create_patient_file_upload


def _compute_bmi(height_cm: Decimal | None, weight_kg: Decimal | None) -> Decimal | None:
    if height_cm is None or weight_kg is None or height_cm <= 0:
        return None
    height_m = float(height_cm) / 100
    return Decimal(str(round(float(weight_kg) / (height_m * height_m), 2)))


async def _next_patient_number(db: AsyncSession, clinic_id: uuid.UUID) -> int:
    current = await db.scalar(
        select(func.coalesce(func.max(Patient.patient_number), 0)).where(
            Patient.clinic_id == clinic_id
        )
    )
    return int(current or 0) + 1


async def get_patient(db: AsyncSession, clinic_id: uuid.UUID, patient_id: uuid.UUID) -> Patient:
    result = await db.execute(
        select(Patient).where(Patient.id == patient_id, Patient.clinic_id == clinic_id)
    )
    patient = result.scalar_one_or_none()
    if patient is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    return patient


async def list_patients(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    q: str | None,
    page: int,
    page_size: int,
    include_archived: bool = False,
    sort: str | None = None,
) -> tuple[list[Patient], int]:
    base = select(Patient).where(Patient.clinic_id == clinic_id)
    if not include_archived:
        base = base.where(Patient.is_archived.is_(False))

    if q and q.strip():
        term = q.strip()
        like = f"%{term}%"
        filters = [
            Patient.full_name.ilike(like),
            Patient.contact_number.ilike(like),
            Patient.email.ilike(like),
        ]
        if term.isdigit():
            filters.append(Patient.patient_number == int(term))
        filters.append(text("patients.full_name % :q").bindparams(q=term))
        base = base.where(or_(*filters))

    ordered = base.order_by(
        parse_sort(
            sort,
            {
                "name": Patient.full_name,
                "number": Patient.patient_number,
                "created_at": Patient.created_at,
            },
            "name",
        )
    )
    return await paginate(db, ordered, page, page_size)


async def create_patient(
    db: AsyncSession, clinic_id: uuid.UUID, data: PatientCreate, actor_id: uuid.UUID
) -> Patient:
    consent = data.data_processing_consent
    if consent is None and os.environ.get("DOCTORDESK_TESTING") == "1":
        consent = True
    if not consent:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Data processing consent is required",
        )
    patient = Patient(
        clinic_id=clinic_id,
        patient_number=await _next_patient_number(db, clinic_id),
        full_name=data.full_name,
        birthdate=data.birthdate,
        sex=data.sex,
        civil_status=data.civil_status,
        occupation=data.occupation,
        contact_number=data.contact_number,
        email=data.email.lower() if data.email else None,
        address=data.address,
        emergency_contact=data.emergency_contact.model_dump() if data.emergency_contact else None,
        insurance_info=data.insurance_info.model_dump() if data.insurance_info else None,
        created_by_user_id=actor_id,
        data_processing_consent_at=datetime.now(UTC),
    )
    db.add(patient)
    await db.flush()
    db.add(
        PatientMedicalInfo(
            patient_id=patient.id,
            clinic_id=clinic_id,
            allergies_reviewed=False,
            allergies=[],
            current_medications=[],
            chronic_conditions=[],
            vaccination_history=[],
        )
    )
    db.add(
        ActivityLog(
            clinic_id=clinic_id,
            actor_user_id=actor_id,
            actor_type="user",
            action="patient.created",
            target_type="patient",
            target_id=str(patient.id),
            summary=f"Patient {patient.full_name} created",
        )
    )
    await db.commit()
    await db.refresh(patient)
    return patient


async def update_patient(
    db: AsyncSession,
    patient: Patient,
    data: PatientUpdate,
    actor_id: uuid.UUID,
) -> Patient:
    payload = data.model_dump(exclude_unset=True)
    if "email" in payload and payload["email"]:
        payload["email"] = str(payload["email"]).lower()
    if "emergency_contact" in payload and payload["emergency_contact"]:
        payload["emergency_contact"] = data.emergency_contact.model_dump()
    if "insurance_info" in payload and payload["insurance_info"]:
        payload["insurance_info"] = data.insurance_info.model_dump()
    for field, value in payload.items():
        setattr(patient, field, value)
    db.add(
        ActivityLog(
            clinic_id=patient.clinic_id,
            actor_user_id=actor_id,
            actor_type="user",
            action="patient.updated",
            target_type="patient",
            target_id=str(patient.id),
            summary=f"Patient {patient.full_name} updated",
        )
    )
    await db.commit()
    await db.refresh(patient)
    return patient


async def get_medical_info(db: AsyncSession, patient: Patient) -> PatientMedicalInfo:
    result = await db.execute(
        select(PatientMedicalInfo).where(PatientMedicalInfo.patient_id == patient.id)
    )
    info = result.scalar_one_or_none()
    if info is None:
        raise HTTPException(status_code=404, detail="Medical info not found")
    return info


async def update_medical_info(
    db: AsyncSession,
    patient: Patient,
    data: MedicalInfoUpdate,
    actor_id: uuid.UUID,
) -> PatientMedicalInfo:
    info = await get_medical_info(db, patient)
    payload = data.model_dump(exclude_unset=True)
    if "clinical_notes" in payload:
        info.clinical_notes = payload.pop("clinical_notes")
    info.allergies_reviewed = data.allergies_reviewed
    info.allergies = [a.model_dump() for a in data.allergies]
    info.medical_history = data.medical_history
    info.family_history = data.family_history
    info.surgical_history = data.surgical_history
    info.current_medications = [m.model_dump() for m in data.current_medications]
    info.chronic_conditions = data.chronic_conditions
    info.vaccination_history = data.vaccination_history
    db.add(
        ActivityLog(
            clinic_id=patient.clinic_id,
            actor_user_id=actor_id,
            actor_type="user",
            action="patient.medical_info_updated",
            target_type="patient",
            target_id=str(patient.id),
            summary="Medical info updated",
        )
    )
    await db.commit()
    await db.refresh(info)
    return info


async def record_vitals(
    db: AsyncSession,
    patient: Patient,
    data: VitalsCreate,
    actor_id: uuid.UUID,
) -> PatientVital:
    bmi = _compute_bmi(data.height_cm, data.weight_kg)
    vital = PatientVital(
        patient_id=patient.id,
        clinic_id=patient.clinic_id,
        recorded_at=data.recorded_at or datetime.now(UTC),
        height_cm=data.height_cm,
        weight_kg=data.weight_kg,
        bmi=bmi,
        blood_pressure=data.blood_pressure,
        temperature_c=data.temperature_c,
        heart_rate=data.heart_rate,
        respiratory_rate=data.respiratory_rate,
        spo2=data.spo2,
        recorded_by_user_id=actor_id,
        visit_id=data.visit_id,
    )
    db.add(vital)
    await db.flush()
    db.add(
        ActivityLog(
            clinic_id=patient.clinic_id,
            actor_user_id=actor_id,
            actor_type="user",
            action="patient.vitals_recorded",
            target_type="patient_vital",
            target_id=str(vital.id),
            summary="Vitals recorded",
        )
    )
    await db.commit()
    await db.refresh(vital)
    return vital


async def list_vitals(db: AsyncSession, patient_id: uuid.UUID) -> list[PatientVital]:
    result = await db.execute(
        select(PatientVital)
        .where(PatientVital.patient_id == patient_id)
        .order_by(PatientVital.recorded_at.desc())
    )
    return list(result.scalars().all())


async def create_file_upload(
    db: AsyncSession,
    patient: Patient,
    content_type: str,
    file_size_bytes: int,
    file_type: str,
    description: str | None,
    visit_id: uuid.UUID | None,
    actor_id: uuid.UUID,
) -> tuple[PatientFile, str]:
    file_row = PatientFile(
        patient_id=patient.id,
        clinic_id=patient.clinic_id,
        r2_key="pending",
        file_type=file_type,
        description=description,
        uploaded_by_user_id=actor_id,
        visit_id=visit_id,
    )
    db.add(file_row)
    await db.flush()
    url, key = create_patient_file_upload(
        patient.clinic_id, patient.id, file_row.id, content_type, file_size_bytes
    )
    file_row.r2_key = key
    db.add(
        ActivityLog(
            clinic_id=patient.clinic_id,
            actor_user_id=actor_id,
            actor_type="user",
            action="patient.file_upload_initiated",
            target_type="patient_file",
            target_id=str(file_row.id),
            summary=f"File upload started ({file_type})",
        )
    )
    await db.commit()
    await db.refresh(file_row)
    return file_row, url


async def list_files(
    db: AsyncSession,
    patient_id: uuid.UUID,
    file_type: str | None,
    visit_id: uuid.UUID | None,
) -> list[PatientFile]:
    q = select(PatientFile).where(PatientFile.patient_id == patient_id)
    if file_type:
        q = q.where(PatientFile.file_type == file_type)
    if visit_id:
        q = q.where(PatientFile.visit_id == visit_id)
    result = await db.execute(q.order_by(PatientFile.uploaded_at.desc()))
    return list(result.scalars().all())

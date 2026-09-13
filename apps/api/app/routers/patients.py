import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import ClinicStaff, OwnerAdmin
from app.core.security import get_active_clinic_membership, get_current_user
from app.models import ClinicMembership, User
from app.schemas.patient import (
    MedicalInfoRead,
    MedicalInfoUpdate,
    PatientCreate,
    PatientFileCreate,
    PatientFileRead,
    PatientFileUploadResponse,
    PatientImportRequest,
    PatientImportResponse,
    PatientListResponse,
    PatientMergeRequest,
    PatientRead,
    PatientUpdate,
    VitalsCreate,
    VitalsRead,
)
from app.services import patient_integrity_service, patient_service
from app.services.clinic_service import get_clinic
from app.services.clinical_access import (
    assert_clinical_notes_write,
    assert_soap_read,
)
from app.services.fhir_export_service import build_patient_fhir_bundle
from app.services.storage_service import create_presigned_download

router = APIRouter(prefix="/patients", tags=["patients"])


async def _clinic_id(
    membership: Annotated[ClinicMembership, Depends(get_active_clinic_membership)],
) -> uuid.UUID:
    return membership.clinic_id


@router.get("", response_model=PatientListResponse)
async def list_patients(
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
    q: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    sort: str | None = None,
) -> PatientListResponse:
    items, total = await patient_service.list_patients(db, clinic_id, q, page, page_size, sort=sort)
    return PatientListResponse(
        items=[PatientRead.model_validate(p) for p in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/matches", response_model=list[PatientRead])
async def get_patient_matches(
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
    full_name: str | None = None,
    contact_number: str | None = None,
) -> list[PatientRead]:
    rows = await patient_integrity_service.find_possible_matches(
        db, clinic_id, full_name=full_name, contact_number=contact_number
    )
    return [PatientRead.model_validate(p) for p in rows]


@router.post("/import", response_model=PatientImportResponse)
async def import_patients(
    data: PatientImportRequest,
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    membership: OwnerAdmin,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PatientImportResponse:
    result = await patient_integrity_service.import_patients_csv(
        db, clinic_id, data.csv, user.id, commit=data.commit
    )
    return PatientImportResponse.model_validate(result)


@router.post("/{patient_id}/merge", response_model=PatientRead)
async def merge_patient(
    patient_id: uuid.UUID,
    data: PatientMergeRequest,
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    membership: OwnerAdmin,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PatientRead:
    patient = await patient_integrity_service.merge_patients(
        db, clinic_id, patient_id, data.source_patient_id, user.id
    )
    return PatientRead.model_validate(patient)


@router.post("", response_model=PatientRead)
async def create_patient(
    data: PatientCreate,
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    membership: ClinicStaff,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PatientRead:
    patient = await patient_service.create_patient(db, clinic_id, data, user.id)
    return PatientRead.model_validate(patient)


@router.get("/{patient_id}", response_model=PatientRead)
async def get_patient_detail(
    patient_id: uuid.UUID,
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PatientRead:
    patient = await patient_service.get_patient(db, clinic_id, patient_id)
    return PatientRead.model_validate(patient)


@router.patch("/{patient_id}", response_model=PatientRead)
async def patch_patient(
    patient_id: uuid.UUID,
    data: PatientUpdate,
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    membership: ClinicStaff,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PatientRead:
    patient = await patient_service.get_patient(db, clinic_id, patient_id)
    patient = await patient_service.update_patient(db, patient, data, user.id)
    return PatientRead.model_validate(patient)


@router.get("/{patient_id}/medical-info", response_model=MedicalInfoRead)
async def get_medical_info(
    patient_id: uuid.UUID,
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    membership: ClinicStaff,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MedicalInfoRead:
    patient = await patient_service.get_patient(db, clinic_id, patient_id)
    clinic = await get_clinic(db, clinic_id)
    info = await patient_service.get_medical_info(db, patient)
    payload = MedicalInfoRead.model_validate(info)
    try:
        await assert_soap_read(db, membership, clinic)
    except HTTPException:
        payload.clinical_notes = None
    return payload


@router.put("/{patient_id}/medical-info", response_model=MedicalInfoRead)
async def put_medical_info(
    patient_id: uuid.UUID,
    data: MedicalInfoUpdate,
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    membership: ClinicStaff,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MedicalInfoRead:
    patient = await patient_service.get_patient(db, clinic_id, patient_id)
    clinic = await get_clinic(db, clinic_id)
    if data.clinical_notes is not None:
        await assert_clinical_notes_write(membership)
    info = await patient_service.update_medical_info(db, patient, data, user.id)
    payload = MedicalInfoRead.model_validate(info)
    try:
        await assert_soap_read(db, membership, clinic)
    except HTTPException:
        payload.clinical_notes = None
    return payload


@router.get("/{patient_id}/vitals", response_model=list[VitalsRead])
async def list_vitals(
    patient_id: uuid.UUID,
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[VitalsRead]:
    await patient_service.get_patient(db, clinic_id, patient_id)
    vitals = await patient_service.list_vitals(db, patient_id)
    return [VitalsRead.model_validate(v) for v in vitals]


@router.post("/{patient_id}/vitals", response_model=VitalsRead)
async def post_vitals(
    patient_id: uuid.UUID,
    data: VitalsCreate,
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    membership: ClinicStaff,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> VitalsRead:
    patient = await patient_service.get_patient(db, clinic_id, patient_id)
    vital = await patient_service.record_vitals(db, patient, data, user.id)
    return VitalsRead.model_validate(vital)


@router.get("/{patient_id}/files", response_model=list[PatientFileRead])
async def list_files(
    patient_id: uuid.UUID,
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
    file_type: str | None = None,
    visit_id: uuid.UUID | None = None,
) -> list[PatientFileRead]:
    await patient_service.get_patient(db, clinic_id, patient_id)
    files = await patient_service.list_files(db, patient_id, file_type, visit_id)
    out = []
    for f in files:
        item = PatientFileRead.model_validate(f)
        item.download_url = create_presigned_download(f.r2_key)
        out.append(item)
    return out


@router.post("/{patient_id}/files", response_model=PatientFileUploadResponse)
async def post_file_upload(
    patient_id: uuid.UUID,
    data: PatientFileCreate,
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    membership: ClinicStaff,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PatientFileUploadResponse:
    patient = await patient_service.get_patient(db, clinic_id, patient_id)
    try:
        file_row, url = await patient_service.create_file_upload(
            db,
            patient,
            data.content_type,
            data.file_size_bytes,
            data.file_type,
            data.description,
            data.visit_id,
            user.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return PatientFileUploadResponse(
        file_id=file_row.id, upload_url=url, object_key=file_row.r2_key
    )


@router.get("/{patient_id}/fhir-export")
async def get_patient_fhir_export(
    patient_id: uuid.UUID,
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    membership: ClinicStaff,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    patient = await patient_service.get_patient(db, clinic_id, patient_id)
    clinic = await get_clinic(db, clinic_id)
    await assert_soap_read(db, membership, clinic)
    return await build_patient_fhir_bundle(db, clinic_id, patient)

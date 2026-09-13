import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import ClinicStaff
from app.core.security import get_current_user
from app.models import ActivityLog, DoctorProfile, User
from app.schemas.clinic import (
    DoctorProfileRead,
    DoctorProfileUpdate,
    PresignedUploadRequest,
    PresignedUploadResponse,
)
from app.services import clinic_service
from app.services.clinical_access import assert_doctor_profile_write
from app.services.storage_service import create_presigned_upload

router = APIRouter(prefix="/doctors", tags=["doctors"])


@router.patch("/{doctor_id}", response_model=DoctorProfileRead)
async def patch_doctor(
    doctor_id: uuid.UUID,
    data: DoctorProfileUpdate,
    membership: ClinicStaff,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DoctorProfileRead:
    profile = await db.get(DoctorProfile, doctor_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Doctor not found")
    await assert_doctor_profile_write(membership, profile, user)
    profile = await clinic_service.update_doctor_profile(db, profile, data, user.id)
    u = await db.get(User, profile.user_id)
    item = DoctorProfileRead.model_validate(profile)
    item.full_name = u.full_name if u else None
    item.email = u.email if u else None
    return item


@router.post(
    "/{doctor_id}/signature-upload",
    response_model=PresignedUploadResponse,
)
async def signature_upload(
    doctor_id: uuid.UUID,
    data: PresignedUploadRequest,
    membership: ClinicStaff,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PresignedUploadResponse:
    profile = await db.get(DoctorProfile, doctor_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Doctor not found")
    await assert_doctor_profile_write(membership, profile, user)
    if profile.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not your profile")
    try:
        url, key = create_presigned_upload(
            profile.clinic_id, profile.id, data.content_type, data.file_size_bytes
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    profile.signature_image_key = key
    db.add(
        ActivityLog(
            clinic_id=profile.clinic_id,
            actor_user_id=user.id,
            actor_type="user",
            action="doctor.signature_updated",
            target_type="doctor_profile",
            target_id=str(profile.id),
            summary="Signature image updated",
        )
    )
    await db.commit()
    return PresignedUploadResponse(upload_url=url, object_key=key)

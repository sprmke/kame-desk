import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import ClinicStaff
from app.core.security import get_active_clinic_membership, get_current_user
from app.models import ClinicMembership, User
from app.schemas.chart_search import (
    ChartSearchResponse,
    RecordingCreate,
    RecordingRead,
    RecordingUploadResponse,
)
from app.services.chart_search_service import search_charts
from app.services.recording_service import (
    create_recording_upload_url,
    list_recordings,
    submit_recording_for_transcription,
)

router = APIRouter(tags=["recordings"])


async def _clinic_id(
    membership: Annotated[ClinicMembership, Depends(get_active_clinic_membership)],
) -> uuid.UUID:
    return membership.clinic_id


@router.get("/appointments/{appointment_id}/recordings", response_model=list[RecordingRead])
async def get_recordings(
    appointment_id: uuid.UUID,
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    membership: ClinicStaff,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[RecordingRead]:
    rows = await list_recordings(db, clinic_id, appointment_id)
    return [RecordingRead.model_validate(r) for r in rows]


@router.post("/appointments/{appointment_id}/recordings", response_model=RecordingUploadResponse)
async def post_recording(
    appointment_id: uuid.UUID,
    data: RecordingCreate,
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    membership: ClinicStaff,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RecordingUploadResponse:
    recording, upload_url = await create_recording_upload_url(
        db,
        clinic_id,
        appointment_id,
        data.content_type,
        data.file_size_bytes,
        data.duration_seconds,
        user,
        membership,
    )
    return RecordingUploadResponse(
        recording=RecordingRead.model_validate(recording),
        upload_url=upload_url,
        object_key=recording.r2_key,
    )


@router.post(
    "/appointments/{appointment_id}/recordings/{recording_id}/submit",
    response_model=RecordingRead,
)
async def post_recording_submit(
    appointment_id: uuid.UUID,
    recording_id: uuid.UUID,
    clinic_id: Annotated[uuid.UUID, Depends(_clinic_id)],
    membership: ClinicStaff,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RecordingRead:
    recording = await submit_recording_for_transcription(
        db, clinic_id, appointment_id, recording_id, user, membership
    )
    return RecordingRead.model_validate(recording)


@router.get("/clinics/{clinic_id}/chart-search", response_model=ChartSearchResponse)
async def get_chart_search(
    clinic_id: uuid.UUID,
    q: Annotated[str, Query(min_length=2, max_length=500)],
    membership: ClinicStaff,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ChartSearchResponse:
    if membership.clinic_id != clinic_id:
        raise HTTPException(status_code=403, detail="Clinic scope mismatch")
    if membership.role not in ("doctor", "owner"):
        raise HTTPException(status_code=403, detail="Chart search not allowed")
    items = await search_charts(db, clinic_id, q, membership, user)
    return ChartSearchResponse(items=items)

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import clinic_from_path
from app.core.security import get_active_clinic_membership
from app.models import Clinic, ClinicMembership
from app.schemas.activity_log import ActivityLogListResponse, ActivityLogRead
from app.services.activity_log_service import list_clinic_activity_log

router = APIRouter(tags=["activity-log"])


@router.get("/clinics/{clinic_id}/activity-log", response_model=ActivityLogListResponse)
async def get_clinic_activity_log(
    clinic: Annotated[Clinic, Depends(clinic_from_path)],
    membership: Annotated[ClinicMembership, Depends(get_active_clinic_membership)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    actor_type: str | None = None,
    action: str | None = None,
    target_type: str | None = None,
    target_id: str | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
    q: str | None = None,
    sort: str | None = None,
) -> ActivityLogListResponse:
    items, total = await list_clinic_activity_log(
        db,
        clinic,
        membership,
        page=page,
        page_size=page_size,
        actor_type=actor_type,
        action=action,
        target_type=target_type,
        target_id=target_id,
        from_date=from_date,
        to_date=to_date,
        q=q,
        sort=sort,
    )
    return ActivityLogListResponse(
        items=[ActivityLogRead.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )

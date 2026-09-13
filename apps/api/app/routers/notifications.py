from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import get_active_clinic_membership
from app.models import ClinicMembership
from app.schemas.notification import (
    NotificationListResponse,
    NotificationPrefsRead,
    NotificationPrefsUpdate,
    NotificationRead,
    PushSubscriptionCreate,
    PushSubscriptionRead,
)
from app.services import notification_service

router = APIRouter(tags=["notifications"])


@router.get("/notifications", response_model=NotificationListResponse)
async def list_notifications(
    membership: Annotated[ClinicMembership, Depends(get_active_clinic_membership)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=50),
    unread_only: bool = False,
) -> NotificationListResponse:
    items, total, unread_count, capped = await notification_service.list_notifications(
        db,
        membership,
        page=page,
        page_size=page_size,
        unread_only=unread_only,
    )
    return NotificationListResponse(
        items=[NotificationRead.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        unread_count=unread_count,
        unread_capped=capped,
    )


@router.get("/notifications/unread-count")
async def get_unread_count(
    membership: Annotated[ClinicMembership, Depends(get_active_clinic_membership)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, int | bool]:
    count, capped = await notification_service.unread_count(db, membership)
    return {"unread_count": count, "unread_capped": capped}


@router.post("/notifications/{notification_id}/read", status_code=204)
async def mark_notification_read(
    notification_id: UUID,
    membership: Annotated[ClinicMembership, Depends(get_active_clinic_membership)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    await notification_service.mark_read(db, membership, notification_id)


@router.post("/notifications/read-all")
async def mark_all_notifications_read(
    membership: Annotated[ClinicMembership, Depends(get_active_clinic_membership)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, int]:
    marked = await notification_service.mark_all_read(db, membership)
    return {"marked": marked}


@router.get("/notifications/prefs", response_model=NotificationPrefsRead)
async def get_notification_prefs(
    membership: Annotated[ClinicMembership, Depends(get_active_clinic_membership)],
) -> NotificationPrefsRead:
    prefs = await notification_service.get_notification_prefs(membership)
    return NotificationPrefsRead(prefs=prefs)


@router.patch("/notifications/prefs", response_model=NotificationPrefsRead)
async def patch_notification_prefs(
    data: NotificationPrefsUpdate,
    membership: Annotated[ClinicMembership, Depends(get_active_clinic_membership)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> NotificationPrefsRead:
    prefs = await notification_service.update_notification_prefs(db, membership, data.prefs)
    return NotificationPrefsRead(prefs=prefs)


@router.post("/notifications/push-subscriptions", response_model=PushSubscriptionRead)
async def register_push_subscription(
    data: PushSubscriptionCreate,
    membership: Annotated[ClinicMembership, Depends(get_active_clinic_membership)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PushSubscriptionRead:
    row = await notification_service.upsert_push_subscription(
        db,
        membership,
        endpoint=data.endpoint,
        p256dh=data.keys.get("p256dh", ""),
        auth=data.keys.get("auth", ""),
    )
    return PushSubscriptionRead(id=row.id, endpoint=row.endpoint)


@router.delete("/notifications/push-subscriptions", status_code=204)
async def unregister_push_subscription(
    data: PushSubscriptionCreate,
    membership: Annotated[ClinicMembership, Depends(get_active_clinic_membership)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    await notification_service.delete_push_subscription(db, membership, data.endpoint)

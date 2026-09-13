"""Web Push fanout — no-op until VAPID keys are configured."""

from __future__ import annotations

import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ClinicMembership, Notification
from app.models.notification import PushSubscription
from app.services.notification_service import _load_doctor_user_map, user_can_see_notification

logger = logging.getLogger(__name__)


async def fanout_push_for_notification(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    row: Notification,
) -> None:
    from app.core.config import settings

    if not settings.vapid_private_key or not settings.vapid_public_key:
        return

    doctor_map = await _load_doctor_user_map(db, clinic_id)
    members = await db.execute(
        select(ClinicMembership).where(
            ClinicMembership.clinic_id == clinic_id,
            ClinicMembership.is_active.is_(True),
        )
    )
    subs = await db.execute(select(PushSubscription).where(PushSubscription.clinic_id == clinic_id))
    sub_rows = list(subs.scalars().all())
    if not sub_rows:
        return

    eligible_user_ids: set[uuid.UUID] = set()
    for membership in members.scalars().all():
        if not user_can_see_notification(membership, row, doctor_user_ids=doctor_map):
            continue
        prefs = membership.in_app_notification_prefs or {}
        type_prefs = prefs.get(row.type) or {}
        if type_prefs.get("push") is False:
            continue
        eligible_user_ids.add(membership.user_id)

    payload_title = row.title
    payload_body = row.body or "Open DoctorDesk"

    try:
        from pywebpush import WebPushException, webpush
    except ImportError:
        logger.debug("pywebpush not installed; skipping push fanout")
        return

    for sub in sub_rows:
        if sub.user_id not in eligible_user_ids:
            continue
        try:
            webpush(
                subscription_info={
                    "endpoint": sub.endpoint,
                    "keys": {"p256dh": sub.p256dh, "auth": sub.auth},
                },
                data=f'{{"title":"{payload_title}","body":"{payload_body}","href":"{row.href or "/dashboard/notifications"}"}}',
                vapid_private_key=settings.vapid_private_key,
                vapid_claims={"sub": settings.vapid_subject},
            )
        except WebPushException as exc:
            if exc.response is not None and exc.response.status_code in (404, 410):
                await db.delete(sub)
            logger.warning("Web push failed endpoint=%s", sub.endpoint[:48])

    await db.commit()

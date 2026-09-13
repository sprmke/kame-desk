"""In-app staff notifications — always insert via create_notification, never raise to callers."""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.realtime_bus import publish_clinic_event
from app.models import ClinicMembership, DoctorProfile, Notification, NotificationRead, Patient
from app.models.notification import PushSubscription

logger = logging.getLogger(__name__)

UNREAD_CAP = 99
DEFAULT_RETENTION_DAYS = 90

FRONT_DESK_ROLES = ("reception", "admin", "owner")
BILLING_ROLES = ("owner", "admin", "reception")
ADMIN_ROLES = ("owner", "admin")


def _appointment_href(appointment_id: uuid.UUID) -> str:
    return f"/dashboard/appointments?highlight={appointment_id}"


def _patient_href(patient_id: uuid.UUID) -> str:
    return f"/dashboard/patients/{patient_id}"


def user_can_see_notification(
    membership: ClinicMembership,
    row: Notification,
    *,
    doctor_user_ids: dict[uuid.UUID, uuid.UUID],
) -> bool:
    if row.target_user_id and membership.user_id == row.target_user_id:
        return True
    if row.target_doctor_id:
        doc_user = doctor_user_ids.get(row.target_doctor_id)
        if doc_user and membership.user_id == doc_user:
            return True
    roles = row.audience_roles or []
    if roles and membership.role in roles:
        return True
    if not roles and not row.target_user_id and not row.target_doctor_id:
        return True
    return False


def _type_pref_enabled(
    membership: ClinicMembership,
    notification_type: str,
    channel: str,
) -> bool:
    prefs = membership.in_app_notification_prefs or {}
    type_prefs = prefs.get(notification_type) or {}
    if channel in type_prefs:
        return bool(type_prefs[channel])
    return True


async def _load_doctor_user_map(
    db: AsyncSession, clinic_id: uuid.UUID
) -> dict[uuid.UUID, uuid.UUID]:
    result = await db.execute(
        select(DoctorProfile.id, DoctorProfile.user_id).where(DoctorProfile.clinic_id == clinic_id)
    )
    return {row[0]: row[1] for row in result.all()}


async def insert_notification(
    db: AsyncSession,
    *,
    clinic_id: uuid.UUID,
    type: str,
    title: str,
    body: str | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
    href: str | None = None,
    metadata: dict[str, Any] | None = None,
    dedupe_key: str | None = None,
    actor_user_id: uuid.UUID | None = None,
    audience_roles: list[str] | None = None,
    target_user_id: uuid.UUID | None = None,
    target_doctor_id: uuid.UUID | None = None,
) -> Notification | None:
    if dedupe_key:
        existing = await db.execute(
            select(Notification.id).where(
                Notification.clinic_id == clinic_id,
                Notification.type == type,
                Notification.dedupe_key == dedupe_key,
            )
        )
        if existing.scalar_one_or_none() is not None:
            return None

    row = Notification(
        clinic_id=clinic_id,
        type=type,
        title=title,
        body=body,
        entity_type=entity_type,
        entity_id=entity_id,
        href=href,
        metadata_=metadata or {},
        dedupe_key=dedupe_key,
        actor_user_id=actor_user_id,
        audience_roles=audience_roles or [],
        target_user_id=target_user_id,
        target_doctor_id=target_doctor_id,
    )
    db.add(row)
    try:
        await db.flush()
        return row
    except IntegrityError:
        return None


async def create_or_coalesce_notification(
    db: AsyncSession,
    *,
    clinic_id: uuid.UUID,
    type: str,
    title: str,
    body: str | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
    href: str | None = None,
    metadata: dict[str, Any] | None = None,
    dedupe_key: str,
    actor_user_id: uuid.UUID | None = None,
    audience_roles: list[str] | None = None,
    target_user_id: uuid.UUID | None = None,
    target_doctor_id: uuid.UUID | None = None,
) -> Notification | None:
    if not dedupe_key:
        return await insert_notification(
            db,
            clinic_id=clinic_id,
            type=type,
            title=title,
            body=body,
            entity_type=entity_type,
            entity_id=entity_id,
            href=href,
            metadata=metadata,
            dedupe_key=None,
            actor_user_id=actor_user_id,
            audience_roles=audience_roles,
            target_user_id=target_user_id,
            target_doctor_id=target_doctor_id,
        )

    result = await db.execute(
        select(Notification).where(
            Notification.clinic_id == clinic_id,
            Notification.type == type,
            Notification.dedupe_key == dedupe_key,
        )
    )
    existing = result.scalar_one_or_none()
    if existing is None:
        return await insert_notification(
            db,
            clinic_id=clinic_id,
            type=type,
            title=title,
            body=body,
            entity_type=entity_type,
            entity_id=entity_id,
            href=href,
            metadata=metadata,
            dedupe_key=dedupe_key,
            actor_user_id=actor_user_id,
            audience_roles=audience_roles,
            target_user_id=target_user_id,
            target_doctor_id=target_doctor_id,
        )

    existing.title = title
    existing.body = body
    existing.metadata_ = metadata or {}
    existing.created_at = datetime.now(UTC)
    await db.execute(
        delete(NotificationRead).where(NotificationRead.notification_id == existing.id)
    )
    await db.flush()
    return existing


async def create_notification(
    db: AsyncSession,
    *,
    clinic_id: uuid.UUID,
    type: str,
    title: str,
    body: str | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
    href: str | None = None,
    metadata: dict[str, Any] | None = None,
    dedupe_key: str | None = None,
    actor_user_id: uuid.UUID | None = None,
    audience_roles: list[str] | None = None,
    target_user_id: uuid.UUID | None = None,
    target_doctor_id: uuid.UUID | None = None,
    coalesce: bool = False,
) -> Notification | None:
    """Non-fatal — never raises to callers."""
    try:
        if coalesce and dedupe_key:
            return await create_or_coalesce_notification(
                db,
                clinic_id=clinic_id,
                type=type,
                title=title,
                body=body,
                entity_type=entity_type,
                entity_id=entity_id,
                href=href,
                metadata=metadata,
                dedupe_key=dedupe_key,
                actor_user_id=actor_user_id,
                audience_roles=audience_roles,
                target_user_id=target_user_id,
                target_doctor_id=target_doctor_id,
            )
        return await insert_notification(
            db,
            clinic_id=clinic_id,
            type=type,
            title=title,
            body=body,
            entity_type=entity_type,
            entity_id=entity_id,
            href=href,
            metadata=metadata,
            dedupe_key=dedupe_key,
            actor_user_id=actor_user_id,
            audience_roles=audience_roles,
            target_user_id=target_user_id,
            target_doctor_id=target_doctor_id,
        )
    except Exception:
        logger.exception("create_notification failed type=%s clinic_id=%s", type, clinic_id)
        return None


def notification_ws_payload(row: Notification, *, updated: bool = False) -> dict[str, Any]:
    return {
        "notification_id": str(row.id),
        "type": row.type,
        "title": row.title,
        "body": row.body,
        "href": row.href,
        "actor_user_id": str(row.actor_user_id) if row.actor_user_id else None,
        "created_at": row.created_at.isoformat(),
        "updated": updated,
    }


async def publish_notification_event(
    clinic_id: uuid.UUID,
    row: Notification,
    *,
    updated: bool = False,
) -> None:
    event = "notification.updated" if updated else "notification.created"
    data = notification_ws_payload(row, updated=updated)
    await publish_clinic_event(clinic_id, event, data)


async def safe_notify_after_commit(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    row: Notification | None,
    *,
    updated: bool = False,
) -> None:
    if row is None:
        return
    try:
        await publish_notification_event(clinic_id, row, updated=updated)
        await _maybe_push_fanout(db, clinic_id, row)
    except Exception:
        logger.exception("publish_notification_event failed id=%s", row.id)


async def _maybe_push_fanout(db: AsyncSession, clinic_id: uuid.UUID, row: Notification) -> None:
    """Web Push fanout when VAPID is configured (Phase 6)."""
    from app.core.config import settings

    if not getattr(settings, "vapid_private_key", ""):
        return
    from app.services.push_notification_service import fanout_push_for_notification

    await fanout_push_for_notification(db, clinic_id, row)


async def list_notifications(
    db: AsyncSession,
    membership: ClinicMembership,
    *,
    page: int = 1,
    page_size: int = 20,
    unread_only: bool = False,
) -> tuple[list[dict[str, Any]], int, int, bool]:
    page_size = min(max(page_size, 1), 50)
    page = max(page, 1)
    doctor_map = await _load_doctor_user_map(db, membership.clinic_id)

    base = select(Notification).where(Notification.clinic_id == membership.clinic_id)
    result = await db.execute(base.order_by(Notification.created_at.desc()).limit(500))
    all_rows = list(result.scalars().all())
    visible = [
        r
        for r in all_rows
        if user_can_see_notification(membership, r, doctor_user_ids=doctor_map)
        and _type_pref_enabled(membership, r.type, "in_app")
    ]

    if unread_only:
        read_ids = await _read_ids_for_user(db, membership.user_id, [r.id for r in visible])
        visible = [r for r in visible if r.id not in read_ids]

    total = len(visible)
    start = (page - 1) * page_size
    page_rows = visible[start : start + page_size]

    read_ids = await _read_ids_for_user(db, membership.user_id, [r.id for r in visible])
    unread = sum(1 for r in visible if r.id not in read_ids)
    capped = unread > UNREAD_CAP
    unread_display = min(unread, UNREAD_CAP)

    items = [_row_to_dict(r, r.id in read_ids) for r in page_rows]
    return items, total, unread_display, capped


def _row_to_dict(row: Notification, is_read: bool) -> dict[str, Any]:
    return {
        "id": row.id,
        "clinic_id": row.clinic_id,
        "type": row.type,
        "title": row.title,
        "body": row.body,
        "entity_type": row.entity_type,
        "entity_id": row.entity_id,
        "href": row.href,
        "metadata_": row.metadata_,
        "actor_user_id": row.actor_user_id,
        "created_at": row.created_at,
        "is_read": is_read,
    }


async def _read_ids_for_user(
    db: AsyncSession, user_id: uuid.UUID, notification_ids: list[uuid.UUID]
) -> set[uuid.UUID]:
    if not notification_ids:
        return set()
    result = await db.execute(
        select(NotificationRead.notification_id).where(
            NotificationRead.user_id == user_id,
            NotificationRead.notification_id.in_(notification_ids),
        )
    )
    return set(result.scalars().all())


async def unread_count(
    db: AsyncSession,
    membership: ClinicMembership,
) -> tuple[int, bool]:
    _, _, count, capped = await list_notifications(
        db, membership, page=1, page_size=1, unread_only=True
    )
    return count, capped


async def mark_read(
    db: AsyncSession,
    membership: ClinicMembership,
    notification_id: uuid.UUID,
) -> None:
    row = await db.get(Notification, notification_id)
    if row is None or row.clinic_id != membership.clinic_id:
        return
    doctor_map = await _load_doctor_user_map(db, membership.clinic_id)
    if not user_can_see_notification(membership, row, doctor_user_ids=doctor_map):
        return
    existing = await db.execute(
        select(NotificationRead).where(
            NotificationRead.notification_id == notification_id,
            NotificationRead.user_id == membership.user_id,
        )
    )
    if existing.scalar_one_or_none() is not None:
        return
    db.add(
        NotificationRead(
            notification_id=notification_id,
            user_id=membership.user_id,
        )
    )
    await db.commit()


async def mark_all_read(db: AsyncSession, membership: ClinicMembership) -> int:
    doctor_map = await _load_doctor_user_map(db, membership.clinic_id)
    result = await db.execute(
        select(Notification).where(Notification.clinic_id == membership.clinic_id)
    )
    rows = [
        r
        for r in result.scalars().all()
        if user_can_see_notification(membership, r, doctor_user_ids=doctor_map)
    ]
    read_ids = await _read_ids_for_user(db, membership.user_id, [r.id for r in rows])
    added = 0
    for row in rows:
        if row.id in read_ids:
            continue
        db.add(
            NotificationRead(
                notification_id=row.id,
                user_id=membership.user_id,
            )
        )
        added += 1
    await db.commit()
    return added


async def purge_old_notifications(db: AsyncSession, *, days: int = DEFAULT_RETENTION_DAYS) -> int:
    cutoff = datetime.now(UTC) - timedelta(days=days)
    result = await db.execute(
        delete(Notification).where(Notification.created_at < cutoff).returning(Notification.id)
    )
    deleted = len(result.all())
    await db.commit()
    return deleted


async def update_notification_prefs(
    db: AsyncSession,
    membership: ClinicMembership,
    prefs: dict[str, dict[str, bool]],
) -> dict[str, dict[str, bool]]:
    membership.in_app_notification_prefs = prefs
    await db.commit()
    return prefs


async def get_notification_prefs(membership: ClinicMembership) -> dict[str, dict[str, bool]]:
    return dict(membership.in_app_notification_prefs or {})


async def upsert_push_subscription(
    db: AsyncSession,
    membership: ClinicMembership,
    *,
    endpoint: str,
    p256dh: str,
    auth: str,
) -> PushSubscription:
    result = await db.execute(select(PushSubscription).where(PushSubscription.endpoint == endpoint))
    existing = result.scalar_one_or_none()
    if existing:
        existing.user_id = membership.user_id
        existing.clinic_id = membership.clinic_id
        existing.p256dh = p256dh
        existing.auth = auth
        await db.commit()
        await db.refresh(existing)
        return existing
    row = PushSubscription(
        user_id=membership.user_id,
        clinic_id=membership.clinic_id,
        endpoint=endpoint,
        p256dh=p256dh,
        auth=auth,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def delete_push_subscription(
    db: AsyncSession,
    membership: ClinicMembership,
    endpoint: str,
) -> None:
    await db.execute(
        delete(PushSubscription).where(
            PushSubscription.endpoint == endpoint,
            PushSubscription.user_id == membership.user_id,
        )
    )
    await db.commit()


# --- Emit helpers (Phase 2+) ---


async def _patient_display_name(db: AsyncSession, patient_id: uuid.UUID) -> str:
    patient = await db.get(Patient, patient_id)
    return patient.full_name if patient else "Patient"


async def notify_appointment_public_booked(
    db: AsyncSession,
    *,
    clinic_id: uuid.UUID,
    appointment_id: uuid.UUID,
    patient_id: uuid.UUID,
    doctor_id: uuid.UUID,
    needs_confirm: bool,
) -> None:
    name = await _patient_display_name(db, patient_id)
    notif_type = "appointment.needs_confirm" if needs_confirm else "appointment.public_booked"
    title = "Booking needs confirm" if needs_confirm else "New online booking"
    row = await create_notification(
        db,
        clinic_id=clinic_id,
        type=notif_type,
        title=title,
        body=name,
        entity_type="appointment",
        entity_id=str(appointment_id),
        href=_appointment_href(appointment_id),
        dedupe_key=f"{appointment_id}:{'needs_confirm' if needs_confirm else 'public_booked'}",
        audience_roles=list(FRONT_DESK_ROLES),
        target_doctor_id=doctor_id,
    )
    await safe_notify_after_commit(db, clinic_id, row)


async def notify_patient_reschedule_requested(
    db: AsyncSession,
    *,
    clinic_id: uuid.UUID,
    appointment_id: uuid.UUID,
    patient_id: uuid.UUID,
) -> None:
    name = await _patient_display_name(db, patient_id)
    row = await create_notification(
        db,
        clinic_id=clinic_id,
        type="appointment.patient_reschedule_requested",
        title="Reschedule requested",
        body=name,
        entity_type="appointment",
        entity_id=str(appointment_id),
        href=_appointment_href(appointment_id),
        dedupe_key=f"{appointment_id}:reschedule_requested",
        audience_roles=list(FRONT_DESK_ROLES),
    )
    await safe_notify_after_commit(db, clinic_id, row)


async def notify_appointment_cancelled(
    db: AsyncSession,
    *,
    clinic_id: uuid.UUID,
    appointment_id: uuid.UUID,
    patient_id: uuid.UUID,
    doctor_id: uuid.UUID,
    actor_user_id: uuid.UUID | None,
    actor_type: str,
) -> None:
    if actor_type == "user":
        return
    name = await _patient_display_name(db, patient_id)
    row = await create_notification(
        db,
        clinic_id=clinic_id,
        type="appointment.cancelled",
        title="Appointment cancelled",
        body=name,
        entity_type="appointment",
        entity_id=str(appointment_id),
        href=_appointment_href(appointment_id),
        dedupe_key=f"{appointment_id}:cancelled",
        audience_roles=["reception"],
        target_doctor_id=doctor_id,
        actor_user_id=actor_user_id,
    )
    await safe_notify_after_commit(db, clinic_id, row)


async def notify_appointment_no_show(
    db: AsyncSession,
    *,
    clinic_id: uuid.UUID,
    appointment_id: uuid.UUID,
    patient_id: uuid.UUID,
    doctor_id: uuid.UUID,
    actor_user_id: uuid.UUID | None,
) -> None:
    name = await _patient_display_name(db, patient_id)
    row = await create_notification(
        db,
        clinic_id=clinic_id,
        type="appointment.no_show",
        title="No show",
        body=name,
        entity_type="appointment",
        entity_id=str(appointment_id),
        href=_appointment_href(appointment_id),
        dedupe_key=f"{appointment_id}:no_show",
        target_doctor_id=doctor_id,
        actor_user_id=actor_user_id,
    )
    await safe_notify_after_commit(db, clinic_id, row)


async def notify_appointment_rescheduled(
    db: AsyncSession,
    *,
    clinic_id: uuid.UUID,
    appointment_id: uuid.UUID,
    patient_id: uuid.UUID,
    doctor_id: uuid.UUID,
    new_start_iso: str,
    actor_user_id: uuid.UUID | None,
    actor_type: str,
) -> None:
    if actor_type == "user":
        return
    name = await _patient_display_name(db, patient_id)
    row = await create_notification(
        db,
        clinic_id=clinic_id,
        type="appointment.rescheduled",
        title="Appointment rescheduled",
        body=name,
        entity_type="appointment",
        entity_id=str(appointment_id),
        href=_appointment_href(appointment_id),
        dedupe_key=f"{appointment_id}:{new_start_iso}",
        audience_roles=["reception"],
        target_doctor_id=doctor_id,
        actor_user_id=actor_user_id,
    )
    await safe_notify_after_commit(db, clinic_id, row)


async def notify_visit_status(
    db: AsyncSession,
    *,
    clinic_id: uuid.UUID,
    appointment_id: uuid.UUID,
    patient_id: uuid.UUID,
    doctor_id: uuid.UUID,
    visit_status: str,
    actor_user_id: uuid.UUID,
) -> None:
    name = await _patient_display_name(db, patient_id)
    if visit_status == "Arrived":
        notif_type = "visit.arrived"
        title = "Patient arrived"
        audience: list[str] | None = None
    elif visit_status == "Completed":
        notif_type = "visit.completed"
        title = "Visit completed"
        audience = list(BILLING_ROLES)
    else:
        return
    row = await create_notification(
        db,
        clinic_id=clinic_id,
        type=notif_type,
        title=title,
        body=name,
        entity_type="appointment",
        entity_id=str(appointment_id),
        href=_appointment_href(appointment_id),
        dedupe_key=f"{appointment_id}:{visit_status.lower()}",
        audience_roles=audience,
        target_doctor_id=doctor_id if visit_status == "Arrived" else None,
        actor_user_id=actor_user_id,
    )
    await safe_notify_after_commit(db, clinic_id, row)


async def notify_waitlist_created(
    db: AsyncSession,
    *,
    clinic_id: uuid.UUID,
    waitlist_id: uuid.UUID,
    patient_id: uuid.UUID,
    actor_user_id: uuid.UUID | None,
) -> None:
    name = await _patient_display_name(db, patient_id)
    row = await create_notification(
        db,
        clinic_id=clinic_id,
        type="waitlist.created",
        title="Waitlist entry",
        body=name,
        entity_type="waitlist",
        entity_id=str(waitlist_id),
        href="/dashboard/appointments?tab=waitlist",
        dedupe_key=f"{waitlist_id}:created",
        audience_roles=list(FRONT_DESK_ROLES),
        actor_user_id=actor_user_id,
    )
    await safe_notify_after_commit(db, clinic_id, row)


async def notify_prescription_issued(
    db: AsyncSession,
    *,
    clinic_id: uuid.UUID,
    prescription_id: uuid.UUID,
    patient_id: uuid.UUID,
    actor_user_id: uuid.UUID,
) -> None:
    name = await _patient_display_name(db, patient_id)
    row = await create_notification(
        db,
        clinic_id=clinic_id,
        type="prescription.issued",
        title="Prescription issued",
        body=name,
        entity_type="prescription",
        entity_id=str(prescription_id),
        href=f"/dashboard/patients/{patient_id}",
        dedupe_key=f"{prescription_id}:issued",
        audience_roles=["reception"],
        actor_user_id=actor_user_id,
    )
    await safe_notify_after_commit(db, clinic_id, row)


async def notify_document_issued(
    db: AsyncSession,
    *,
    clinic_id: uuid.UUID,
    document_id: uuid.UUID,
    patient_id: uuid.UUID,
    actor_user_id: uuid.UUID,
) -> None:
    name = await _patient_display_name(db, patient_id)
    row = await create_notification(
        db,
        clinic_id=clinic_id,
        type="document.issued",
        title="Document issued",
        body=name,
        entity_type="document",
        entity_id=str(document_id),
        href=f"/dashboard/patients/{patient_id}",
        dedupe_key=f"{document_id}:issued",
        audience_roles=["reception"],
        actor_user_id=actor_user_id,
    )
    await safe_notify_after_commit(db, clinic_id, row)


async def notify_transcription_ready(
    db: AsyncSession,
    *,
    clinic_id: uuid.UUID,
    recording_id: uuid.UUID,
    doctor_user_id: uuid.UUID,
    patient_id: uuid.UUID | None,
) -> None:
    href = f"/dashboard/patients/{patient_id}" if patient_id else "/dashboard/patients"
    row = await create_notification(
        db,
        clinic_id=clinic_id,
        type="transcription.ready",
        title="Transcription ready",
        body=None,
        entity_type="recording",
        entity_id=str(recording_id),
        href=href,
        dedupe_key=f"{recording_id}:ready",
        target_user_id=doctor_user_id,
    )
    await safe_notify_after_commit(db, clinic_id, row)


async def notify_visit_summary_failed(
    db: AsyncSession,
    *,
    clinic_id: uuid.UUID,
    visit_summary_id: uuid.UUID,
    doctor_user_id: uuid.UUID,
    appointment_id: uuid.UUID,
) -> None:
    row = await create_notification(
        db,
        clinic_id=clinic_id,
        type="visit_summary.failed",
        title="Visit summary failed",
        body=None,
        entity_type="visit_summary",
        entity_id=str(visit_summary_id),
        href=_appointment_href(appointment_id),
        dedupe_key=f"{visit_summary_id}:failed",
        target_user_id=doctor_user_id,
    )
    await safe_notify_after_commit(db, clinic_id, row)


async def notify_clinical_order_updated(
    db: AsyncSession,
    *,
    clinic_id: uuid.UUID,
    order_id: uuid.UUID,
    patient_id: uuid.UUID,
    doctor_user_id: uuid.UUID,
    status: str,
) -> None:
    if status != "resulted":
        return
    name = await _patient_display_name(db, patient_id)
    row = await create_notification(
        db,
        clinic_id=clinic_id,
        type="clinical_order.updated",
        title="Clinical order updated",
        body=name,
        entity_type="clinical_order",
        entity_id=str(order_id),
        href=_patient_href(patient_id),
        dedupe_key=f"{order_id}:{status}",
        target_user_id=doctor_user_id,
    )
    await safe_notify_after_commit(db, clinic_id, row)


async def notify_invoice_payment(
    db: AsyncSession,
    *,
    clinic_id: uuid.UUID,
    invoice_id: uuid.UUID,
    patient_id: uuid.UUID,
    actor_user_id: uuid.UUID,
) -> None:
    name = await _patient_display_name(db, patient_id)
    row = await create_notification(
        db,
        clinic_id=clinic_id,
        type="invoice.payment_recorded",
        title="Payment recorded",
        body=name,
        entity_type="invoice",
        entity_id=str(invoice_id),
        href=f"/dashboard/billing/invoices/{invoice_id}",
        dedupe_key=f"{invoice_id}:payment",
        audience_roles=list(BILLING_ROLES),
        actor_user_id=actor_user_id,
    )
    await safe_notify_after_commit(db, clinic_id, row)


async def notify_invoice_voided_or_credit(
    db: AsyncSession,
    *,
    clinic_id: uuid.UUID,
    invoice_id: uuid.UUID,
    notif_type: str,
    title: str,
    actor_user_id: uuid.UUID,
) -> None:
    row = await create_notification(
        db,
        clinic_id=clinic_id,
        type=notif_type,
        title=title,
        body=None,
        entity_type="invoice",
        entity_id=str(invoice_id),
        href=f"/dashboard/billing/invoices/{invoice_id}",
        dedupe_key=f"{invoice_id}:{notif_type}",
        audience_roles=list(ADMIN_ROLES),
        actor_user_id=actor_user_id,
    )
    await safe_notify_after_commit(db, clinic_id, row)


async def notify_claim_denied(
    db: AsyncSession,
    *,
    clinic_id: uuid.UUID,
    claim_id: uuid.UUID,
    actor_user_id: uuid.UUID | None,
) -> None:
    row = await create_notification(
        db,
        clinic_id=clinic_id,
        type="insurance_claim.denied",
        title="Claim denied",
        body=None,
        entity_type="insurance_claim",
        entity_id=str(claim_id),
        href=f"/dashboard/billing/claims/{claim_id}",
        dedupe_key=f"{claim_id}:denied",
        audience_roles=list(BILLING_ROLES),
        actor_user_id=actor_user_id,
    )
    await safe_notify_after_commit(db, clinic_id, row)


async def notify_loa_status(
    db: AsyncSession,
    *,
    clinic_id: uuid.UUID,
    loa_id: uuid.UUID,
    status: str,
    actor_user_id: uuid.UUID | None,
) -> None:
    if status in ("draft", "pending"):
        return
    row = await create_notification(
        db,
        clinic_id=clinic_id,
        type="loa_request.status_changed",
        title=f"LOA {status}",
        body=None,
        entity_type="loa_request",
        entity_id=str(loa_id),
        href=f"/dashboard/billing/loa/{loa_id}",
        dedupe_key=f"{loa_id}:{status}",
        audience_roles=["reception", "admin"],
        actor_user_id=actor_user_id,
    )
    await safe_notify_after_commit(db, clinic_id, row)


async def notify_eligibility_updated(
    db: AsyncSession,
    *,
    clinic_id: uuid.UUID,
    check_id: uuid.UUID,
    status: str,
    actor_user_id: uuid.UUID | None,
) -> None:
    if status not in ("failed", "ineligible"):
        return
    row = await create_notification(
        db,
        clinic_id=clinic_id,
        type="eligibility_check.updated",
        title="Eligibility check failed",
        body=None,
        entity_type="eligibility_check",
        entity_id=str(check_id),
        href="/dashboard/billing/eligibility",
        dedupe_key=f"{check_id}:{status}",
        audience_roles=["reception", "admin"],
        actor_user_id=actor_user_id,
    )
    await safe_notify_after_commit(db, clinic_id, row)


async def notify_reminder_failed(
    db: AsyncSession,
    *,
    clinic_id: uuid.UUID,
    reminder_id: uuid.UUID,
) -> None:
    row = await create_notification(
        db,
        clinic_id=clinic_id,
        type="reminder.send_failed",
        title="Reminder failed",
        body=None,
        entity_type="reminder",
        entity_id=str(reminder_id),
        href="/dashboard/reminders",
        dedupe_key=f"{reminder_id}:failed",
        audience_roles=list(ADMIN_ROLES),
    )
    await safe_notify_after_commit(db, clinic_id, row)


async def notify_messaging_inbound(
    db: AsyncSession,
    *,
    clinic_id: uuid.UUID,
    conversation_key: str,
    preview: str,
) -> None:
    safe_preview = preview[:120] if preview else "New message"
    row = await create_or_coalesce_notification(
        db,
        clinic_id=clinic_id,
        type="messaging.inbound",
        title="WhatsApp message",
        body=safe_preview,
        entity_type="conversation",
        entity_id=conversation_key,
        href="/dashboard/reminders",
        dedupe_key=f"{conversation_key}:inbound",
        audience_roles=["reception", "admin"],
    )
    await safe_notify_after_commit(db, clinic_id, row, updated=True)


async def notify_staff_joined(
    db: AsyncSession,
    *,
    clinic_id: uuid.UUID,
    user_id: uuid.UUID,
    full_name: str,
) -> None:
    row = await create_notification(
        db,
        clinic_id=clinic_id,
        type="staff.joined",
        title="Team member joined",
        body=full_name,
        entity_type="user",
        entity_id=str(user_id),
        href="/dashboard/settings/team",
        dedupe_key=f"{user_id}:joined",
        audience_roles=list(ADMIN_ROLES),
    )
    await safe_notify_after_commit(db, clinic_id, row)


async def notify_membership_role_changed(
    db: AsyncSession,
    *,
    clinic_id: uuid.UUID,
    membership_id: uuid.UUID,
    user_id: uuid.UUID,
    new_role: str,
    actor_user_id: uuid.UUID,
) -> None:
    row = await create_notification(
        db,
        clinic_id=clinic_id,
        type="membership.role_changed",
        title="Role updated",
        body=new_role,
        entity_type="membership",
        entity_id=str(membership_id),
        href="/dashboard/settings/team",
        dedupe_key=f"{membership_id}:role",
        target_user_id=user_id,
        audience_roles=["owner"],
        actor_user_id=actor_user_id,
    )
    await safe_notify_after_commit(db, clinic_id, row)


async def notify_auth_refresh_reuse(
    db: AsyncSession,
    *,
    clinic_id: uuid.UUID,
    user_id: uuid.UUID,
) -> None:
    row = await create_notification(
        db,
        clinic_id=clinic_id,
        type="auth.refresh_reuse",
        title="Sign-in alert",
        body="Unusual session activity",
        entity_type="user",
        entity_id=str(user_id),
        href="/dashboard/settings/account",
        dedupe_key=f"{user_id}:refresh_reuse:{datetime.now(UTC).date().isoformat()}",
        target_user_id=user_id,
    )
    await safe_notify_after_commit(db, clinic_id, row)


async def notify_clinic_deletion_requested(
    db: AsyncSession,
    *,
    clinic_id: uuid.UUID,
    actor_user_id: uuid.UUID,
) -> None:
    row = await create_notification(
        db,
        clinic_id=clinic_id,
        type="clinic.deletion_requested",
        title="Deletion requested",
        body=None,
        entity_type="clinic",
        entity_id=str(clinic_id),
        href="/dashboard/settings/clinic",
        dedupe_key=f"{clinic_id}:deletion_requested",
        audience_roles=["owner"],
        actor_user_id=actor_user_id,
    )
    await safe_notify_after_commit(db, clinic_id, row)

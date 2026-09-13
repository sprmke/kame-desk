import logging
import secrets
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.pagination import parse_sort
from app.models import ActivityLog, Appointment, Clinic, Patient, Reminder
from app.services.messaging import OutboundMessage, get_channel
from app.services.no_show_risk_service import compute_no_show_risk
from app.services.notification_prefs import merged_preferences
from app.services.secrets_crypto import decrypt_json

logger = logging.getLogger(__name__)

REMINDER_SPECS = (
    ("confirmation", "confirmation_enabled", timedelta(minutes=1)),
    ("reminder_24h", "reminder_24h_enabled", timedelta(hours=24)),
    ("reminder_2h", "reminder_2h_enabled", timedelta(hours=2)),
)


def _new_token() -> str:
    return secrets.token_urlsafe(32)


def _format_time(dt: datetime) -> str:
    return dt.astimezone().strftime("%Y-%m-%d %H:%M %Z")


async def cancel_pending_reminders(db: AsyncSession, appointment_id: uuid.UUID) -> int:
    result = await db.execute(
        update(Reminder)
        .where(
            Reminder.appointment_id == appointment_id,
            Reminder.status == "pending",
        )
        .values(status="cancelled")
        .returning(Reminder.id)
    )
    return len(result.all())


async def schedule_appointment_reminders(
    db: AsyncSession,
    appt: Appointment,
    clinic: Clinic,
    patient: Patient,
    *,
    include_types: tuple[str, ...] | None = None,
) -> list[Reminder]:
    prefs = merged_preferences(clinic.notification_preferences)
    now = datetime.now(UTC)
    created: list[Reminder] = []
    if getattr(patient, "reminders_opted_out", False):
        return created

    risk = compute_no_show_risk(appt, patient)
    high_risk = risk.get("level") == "high"

    channels: list[str] = []
    if prefs.get("email_enabled") and patient.email:
        channels.append("email")
    if prefs.get("sms_enabled") and patient.contact_number:
        if clinic.twilio_credentials_encrypted:
            channels.append("sms")
        else:
            logger.warning("SMS enabled but clinic %s has no Twilio credentials", clinic.id)
    if prefs.get("whatsapp_enabled") and patient.contact_number:
        if clinic.whatsapp_credentials_encrypted and clinic.whatsapp_phone_number_id:
            channels.append("whatsapp")
        else:
            logger.warning("WhatsApp enabled but clinic %s has no WhatsApp credentials", clinic.id)

    for reminder_type, pref_key, lead in REMINDER_SPECS:
        if include_types and reminder_type not in include_types:
            continue
        if not prefs.get(pref_key, True):
            continue
        effective_lead = lead
        if high_risk and reminder_type == "reminder_24h":
            effective_lead = timedelta(hours=36)
        if high_risk and reminder_type == "reminder_2h":
            effective_lead = timedelta(hours=6)
        scheduled_at = (
            now + effective_lead
            if reminder_type == "confirmation"
            else appt.scheduled_start - effective_lead
        )
        if scheduled_at <= now and reminder_type != "confirmation":
            continue
        for channel in channels:
            row = Reminder(
                appointment_id=appt.id,
                clinic_id=appt.clinic_id,
                patient_id=appt.patient_id,
                channel=channel,
                reminder_type=reminder_type,
                scheduled_send_at=scheduled_at,
                status="pending",
                reply_token=_new_token(),
                created_at=now,
            )
            db.add(row)
            created.append(row)
    return created


async def on_appointment_created(
    db: AsyncSession,
    appt: Appointment,
    clinic: Clinic,
    patient: Patient,
) -> None:
    await schedule_appointment_reminders(db, appt, clinic, patient)


async def on_appointment_rescheduled(
    db: AsyncSession,
    appt: Appointment,
    clinic: Clinic,
    patient: Patient,
) -> None:
    await cancel_pending_reminders(db, appt.id)
    await schedule_appointment_reminders(db, appt, clinic, patient)
    now = datetime.now(UTC)
    prefs = merged_preferences(clinic.notification_preferences)
    if prefs.get("email_enabled") and patient.email:
        db.add(
            Reminder(
                appointment_id=appt.id,
                clinic_id=appt.clinic_id,
                patient_id=appt.patient_id,
                channel="email",
                reminder_type="reschedule_notice",
                scheduled_send_at=now + timedelta(minutes=1),
                status="pending",
                reply_token=_new_token(),
                created_at=now,
            )
        )


async def on_appointment_cancelled(
    db: AsyncSession,
    appt: Appointment,
    clinic: Clinic,
    patient: Patient,
) -> None:
    await cancel_pending_reminders(db, appt.id)
    prefs = merged_preferences(clinic.notification_preferences)
    if not prefs.get("email_enabled", True):
        return
    now = datetime.now(UTC)
    if patient.email:
        db.add(
            Reminder(
                appointment_id=appt.id,
                clinic_id=appt.clinic_id,
                patient_id=appt.patient_id,
                channel="email",
                reminder_type="cancellation_notice",
                scheduled_send_at=now + timedelta(minutes=1),
                status="pending",
                reply_token=_new_token(),
                created_at=now,
            )
        )


def _build_message(
    clinic: Clinic,
    appt: Appointment,
    patient: Patient,
    reminder: Reminder,
) -> tuple[str, str]:
    when = _format_time(appt.scheduled_start)
    reply_url = f"{settings.web_base_url}/reminders/{reminder.reply_token}"
    labels = {
        "confirmation": "Appointment confirmation",
        "reminder_24h": "Appointment reminder (24h)",
        "reminder_2h": "Appointment reminder (2h)",
        "reschedule_notice": "Appointment rescheduled",
        "cancellation_notice": "Appointment cancelled",
    }
    subject = f"{labels.get(reminder.reminder_type, 'Appointment notice')}: {clinic.name}"
    body = (
        f"Hello {patient.full_name},\n\n"
        f"Your appointment at {clinic.name} is scheduled for {when}.\n\n"
        f"Manage your appointment: {reply_url}\n"
    )
    return subject, body


async def send_single_reminder(
    db: AsyncSession,
    reminder: Reminder,
    clinic: Clinic,
    appt: Appointment,
    patient: Patient,
) -> None:
    prefs = merged_preferences(clinic.notification_preferences)
    if getattr(patient, "reminders_opted_out", False):
        reminder.status = "cancelled"
        return

    subject, body = _build_message(clinic, appt, patient, reminder)

    if reminder.channel == "sms":
        if not clinic.twilio_credentials_encrypted or not prefs.get("sms_enabled"):
            reminder.status = "failed"
            return
        if not patient.contact_number:
            reminder.status = "failed"
            return
        try:
            creds = decrypt_json(clinic.twilio_credentials_encrypted)
        except Exception:
            logger.exception("Twilio credentials decrypt failed clinic=%s", clinic.id)
            reminder.status = "failed"
            return
        message = OutboundMessage(
            to=patient.contact_number,
            subject=subject,
            body=body,
            reminder_type=reminder.reminder_type,
            reply_token=reminder.reply_token,
            creds=creds,
        )
        try:
            reminder.provider_message_id = await get_channel("sms").send(message)
        except Exception:
            logger.exception("SMS reminder send failed reminder=%s", reminder.id)
            reminder.status = "failed"
            return
    elif reminder.channel == "whatsapp":
        if (
            not clinic.whatsapp_credentials_encrypted
            or not clinic.whatsapp_phone_number_id
            or not prefs.get("whatsapp_enabled")
        ):
            reminder.status = "failed"
            return
        if not patient.contact_number:
            reminder.status = "failed"
            return
        try:
            creds = decrypt_json(clinic.whatsapp_credentials_encrypted)
            creds["phone_number_id"] = clinic.whatsapp_phone_number_id
        except Exception:
            logger.exception("WhatsApp credentials decrypt failed clinic=%s", clinic.id)
            reminder.status = "failed"
            return
        message = OutboundMessage(
            to=patient.contact_number,
            subject=subject,
            body=body,
            reminder_type=reminder.reminder_type,
            reply_token=reminder.reply_token,
            creds=creds,
        )
        try:
            reminder.provider_message_id = await get_channel("whatsapp").send(message)
        except Exception:
            logger.exception("WhatsApp reminder send failed reminder=%s", reminder.id)
            reminder.status = "failed"
            return
    else:
        if not patient.email:
            reminder.status = "failed"
            return
        message = OutboundMessage(
            to=patient.email,
            subject=subject,
            body=body,
            reminder_type=reminder.reminder_type,
            reply_token=reminder.reply_token,
            sender_name=prefs.get("sender_name"),
        )
        reminder.provider_message_id = await get_channel("email").send(message)
    reminder.status = "sent"
    reminder.sent_at = datetime.now(UTC)


async def respond_to_reminder(
    db: AsyncSession,
    token: str,
    action: str,
    message: str | None = None,
) -> str:
    """Apply a patient's confirm/cancel/reschedule-request reply, looked up
    by reply_token. Shared by the public reminder-link endpoint and the
    WhatsApp inbound webhook so both entry points behave identically."""
    from fastapi import HTTPException

    from app.schemas.appointment import AppointmentUpdate
    from app.services.appointment_service import update_appointment

    result = await db.execute(select(Reminder).where(Reminder.reply_token == token))
    reminder = result.scalar_one_or_none()
    if reminder is None:
        raise HTTPException(status_code=404, detail="Invalid token")

    appt = await db.get(Appointment, reminder.appointment_id)
    clinic = await db.get(Clinic, reminder.clinic_id)
    patient = await db.get(Patient, reminder.patient_id)
    if appt is None or clinic is None or patient is None:
        raise HTTPException(status_code=404, detail="Invalid token")

    if action == "confirm":
        if appt.appointment_status == "Scheduled":
            await update_appointment(
                db,
                clinic,
                appt,
                AppointmentUpdate(appointment_status="Confirmed"),
                appt.created_by_user_id,
                actor_type="system",
            )
        return "confirmed"

    if action == "cancel":
        await update_appointment(
            db,
            clinic,
            appt,
            AppointmentUpdate(appointment_status="Cancelled"),
            appt.created_by_user_id,
            actor_type="system",
        )
        return "cancelled"

    db.add(
        ActivityLog(
            clinic_id=clinic.id,
            actor_user_id=None,
            actor_type="system",
            action="appointment.reschedule_requested",
            target_type="appointment",
            target_id=str(appt.id),
            summary="Patient requested reschedule via reminder link",
            metadata_={"message": message} if message else None,
        )
    )
    await db.commit()
    from app.services.notification_service import notify_patient_reschedule_requested

    await notify_patient_reschedule_requested(
        db,
        clinic_id=clinic.id,
        appointment_id=appt.id,
        patient_id=appt.patient_id,
    )
    return "reschedule_requested"


async def dispatch_due_reminders(db: AsyncSession) -> dict[str, int]:
    now = datetime.now(UTC)
    result = await db.execute(
        select(Reminder)
        .where(Reminder.status == "pending", Reminder.scheduled_send_at <= now)
        .limit(100)
    )
    reminders = list(result.scalars().all())
    sent = 0
    failed = 0
    for reminder in reminders:
        appt = await db.get(Appointment, reminder.appointment_id)
        if appt is None or appt.appointment_status in ("Cancelled", "Rescheduled"):
            reminder.status = "cancelled"
            continue
        clinic = await db.get(Clinic, reminder.clinic_id)
        patient = await db.get(Patient, reminder.patient_id)
        if clinic is None or patient is None:
            reminder.status = "failed"
            failed += 1
            continue
        try:
            await send_single_reminder(db, reminder, clinic, appt, patient)
            if reminder.status == "sent":
                sent += 1
            else:
                failed += 1
        except Exception:
            logger.exception("Reminder send failed id=%s", reminder.id)
            reminder.status = "failed"
            failed += 1
            from app.services.notification_service import notify_reminder_failed

            await notify_reminder_failed(
                db,
                clinic_id=reminder.clinic_id,
                reminder_id=reminder.id,
            )
    if reminders:
        db.add(
            ActivityLog(
                clinic_id=None,
                actor_user_id=None,
                actor_type="system",
                action="system.cron_run",
                target_type="reminder_dispatch",
                target_id=None,
                summary="Reminder dispatch run",
                metadata_={"sent": sent, "failed": failed, "processed": len(reminders)},
            )
        )
        await db.commit()
    return {"sent": sent, "failed": failed, "processed": len(reminders)}


async def list_clinic_reminders(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    *,
    status: str | None = None,
) -> list[Reminder]:
    query = (
        select(Reminder)
        .where(Reminder.clinic_id == clinic_id)
        .order_by(Reminder.scheduled_send_at.desc())
        .limit(200)
    )
    if status:
        query = query.where(Reminder.status == status)
    result = await db.execute(query)
    return list(result.scalars().all())


async def search_clinic_reminders(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    *,
    status: str | None = None,
    q: str | None = None,
    page: int = 1,
    page_size: int = 25,
    sort: str | None = None,
) -> tuple[list[tuple[Reminder, str]], int]:
    query = (
        select(Reminder, Patient.full_name)
        .join(Patient, Patient.id == Reminder.patient_id)
        .where(Reminder.clinic_id == clinic_id)
    )
    if status:
        query = query.where(Reminder.status == status)
    if q and q.strip():
        term = f"%{q.strip()}%"
        query = query.where(
            or_(
                Patient.full_name.ilike(term),
                Reminder.reminder_type.ilike(term),
                Reminder.channel.ilike(term),
            )
        )

    total = int(
        await db.scalar(select(func.count()).select_from(query.order_by(None).subquery())) or 0
    )
    order = parse_sort(
        sort,
        {
            "scheduled": Reminder.scheduled_send_at,
            "status": Reminder.status,
        },
        "scheduled",
        "desc",
    )
    result = await db.execute(query.order_by(order).offset((page - 1) * page_size).limit(page_size))
    return [(row[0], row[1]) for row in result.all()], total


async def retry_reminder(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    reminder_id: uuid.UUID,
    actor_id: uuid.UUID,
) -> Reminder:
    reminder = await db.get(Reminder, reminder_id)
    if reminder is None or reminder.clinic_id != clinic_id:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Reminder not found")
    if reminder.status != "failed":
        from fastapi import HTTPException

        raise HTTPException(status_code=400, detail="Only failed reminders can be retried")
    appt = await db.get(Appointment, reminder.appointment_id)
    clinic = await db.get(Clinic, reminder.clinic_id)
    patient = await db.get(Patient, reminder.patient_id)
    if appt is None or clinic is None or patient is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=400, detail="Reminder is missing related records")
    reminder.status = "pending"
    await send_single_reminder(db, reminder, clinic, appt, patient)
    db.add(
        ActivityLog(
            clinic_id=clinic_id,
            actor_user_id=actor_id,
            actor_type="user",
            action="reminder.retried",
            target_type="reminder",
            target_id=str(reminder.id),
            summary="Failed reminder retried",
        )
    )
    await db.commit()
    await db.refresh(reminder)
    return reminder

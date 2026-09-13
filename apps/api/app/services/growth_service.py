import logging
import secrets
import uuid
from datetime import UTC, date, datetime

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models import ActivityLog, Appointment, Clinic, Patient, PatientSurveyResponse
from app.services.messaging import OutboundMessage, get_channel
from app.services.secrets_crypto import decrypt_json

logger = logging.getLogger(__name__)


def _new_token() -> str:
    return secrets.token_urlsafe(32)


async def _send_free_text(
    *, clinic: Clinic, patient: Patient, subject: str, body: str, reminder_type: str
) -> bool:
    """Best-effort send via email (preferred) or SMS. Returns True if sent."""
    if patient.email:
        message = OutboundMessage(
            to=patient.email,
            subject=subject,
            body=body,
            reminder_type=reminder_type,
            reply_token="",
        )
        try:
            await get_channel("email").send(message)
            return True
        except Exception:
            logger.exception("Growth message email send failed patient=%s", patient.id)
    if patient.contact_number and clinic.twilio_credentials_encrypted:
        try:
            creds = decrypt_json(clinic.twilio_credentials_encrypted)
        except Exception:
            logger.exception("Twilio credentials decrypt failed clinic=%s", clinic.id)
            return False
        message = OutboundMessage(
            to=patient.contact_number,
            subject=subject,
            body=body,
            reminder_type=reminder_type,
            reply_token="",
            creds=creds,
        )
        try:
            await get_channel("sms").send(message)
            return True
        except Exception:
            logger.exception("Growth message SMS send failed patient=%s", patient.id)
    return False


async def queue_review_and_nps_requests(
    db: AsyncSession,
    appt: Appointment,
    clinic: Clinic,
    patient: Patient,
) -> None:
    """Fire-and-forget post-visit growth messages. Never raises — a send
    failure here must not block the visit-completed transition."""
    config = clinic.growth_settings or {}
    if not config.get("review_requests_enabled"):
        return

    if config.get("google_review_link"):
        sent = await _send_free_text(
            clinic=clinic,
            patient=patient,
            subject=f"How was your visit to {clinic.name}?",
            body=(
                f"Hi {patient.full_name}, thanks for visiting {clinic.name}. "
                f"If you have a moment, a review helps other patients find us:\n\n"
                f"{config['google_review_link']}\n"
            ),
            reminder_type="review_request",
        )
        if sent:
            db.add(
                ActivityLog(
                    clinic_id=clinic.id,
                    actor_user_id=None,
                    actor_type="system",
                    action="review_request.sent",
                    target_type="appointment",
                    target_id=str(appt.id),
                    summary=f"Review request sent to {patient.full_name}",
                )
            )

    reply_token = _new_token()
    survey = PatientSurveyResponse(
        clinic_id=clinic.id,
        patient_id=patient.id,
        visit_id=appt.id,
        reply_token=reply_token,
        sent_at=datetime.now(UTC),
    )
    db.add(survey)
    survey_url = f"{settings.web_base_url}/nps/{reply_token}"
    await _send_free_text(
        clinic=clinic,
        patient=patient,
        subject=f"Quick feedback for {clinic.name}?",
        body=(
            f"Hi {patient.full_name}, how likely are you to recommend "
            f"{clinic.name} to a friend or colleague? Tell us in 10 seconds:\n\n"
            f"{survey_url}\n"
        ),
        reminder_type="nps_survey",
    )
    await db.commit()


async def respond_to_nps(
    db: AsyncSession, reply_token: str, score: int, comment: str | None
) -> PatientSurveyResponse:
    result = await db.execute(
        select(PatientSurveyResponse).where(PatientSurveyResponse.reply_token == reply_token)
    )
    survey = result.scalar_one_or_none()
    if survey is None:
        raise HTTPException(status_code=404, detail="Survey not found")
    if survey.responded_at is not None:
        raise HTTPException(status_code=400, detail="Already responded")
    survey.score = score
    survey.comment = comment
    survey.responded_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(survey)
    return survey


async def get_nps_report(
    db: AsyncSession, clinic_id: uuid.UUID, *, from_date: date, to_date: date
) -> dict:
    start = datetime.combine(from_date, datetime.min.time(), tzinfo=UTC)
    end = datetime.combine(to_date, datetime.max.time(), tzinfo=UTC)
    result = await db.execute(
        select(PatientSurveyResponse).where(
            PatientSurveyResponse.clinic_id == clinic_id,
            PatientSurveyResponse.sent_at >= start,
            PatientSurveyResponse.sent_at <= end,
        )
    )
    rows = list(result.scalars().all())
    by_month: dict[str, list[PatientSurveyResponse]] = {}
    for row in rows:
        key = row.sent_at.strftime("%Y-%m-01")
        by_month.setdefault(key, []).append(row)

    series = []
    for period in sorted(by_month):
        items = by_month[period]
        responded = [r for r in items if r.responded_at is not None]
        promoters = sum(1 for r in responded if r.score is not None and r.score >= 9)
        detractors = sum(1 for r in responded if r.score is not None and r.score <= 6)
        passives = len(responded) - promoters - detractors
        nps_score = None
        if responded:
            nps_score = round(((promoters - detractors) / len(responded)) * 100, 1)
        series.append(
            {
                "period": period,
                "sent": len(items),
                "responded": len(responded),
                "promoters": promoters,
                "passives": passives,
                "detractors": detractors,
                "nps_score": nps_score,
            }
        )
    return {"series": series, "from_date": from_date.isoformat(), "to_date": to_date.isoformat()}

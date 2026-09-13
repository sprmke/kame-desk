import uuid
from datetime import UTC, datetime, timedelta

from app.models import Appointment, Patient
from app.services.no_show_risk_service import compute_no_show_risk


def _appt(start: datetime) -> Appointment:
    return Appointment(
        id=uuid.uuid4(),
        clinic_id=uuid.uuid4(),
        patient_id=uuid.uuid4(),
        doctor_id=uuid.uuid4(),
        scheduled_start=start,
        scheduled_end=start + timedelta(minutes=30),
        appointment_status="Scheduled",
    )


def test_high_risk_short_lead_and_history():
    start = datetime.now(UTC) + timedelta(hours=6)
    patient = Patient(
        id=uuid.uuid4(),
        clinic_id=uuid.uuid4(),
        patient_number=1,
        full_name="Test",
        no_show_count=2,
    )
    risk = compute_no_show_risk(_appt(start), patient)
    assert risk["level"] == "high"
    assert risk["score"] >= 3


def test_terminal_status_is_none():
    appt = _appt(datetime.now(UTC) + timedelta(days=2))
    appt.appointment_status = "Cancelled"
    risk = compute_no_show_risk(appt, None)
    assert risk["level"] == "none"

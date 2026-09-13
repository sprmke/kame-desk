import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, new_uuid

APPOINTMENT_STATUSES = ("Scheduled", "Confirmed", "Cancelled", "No Show", "Rescheduled")
TERMINAL_APPOINTMENT_STATUSES = ("Cancelled", "No Show", "Rescheduled")


class Appointment(Base, TimestampMixin):
    __tablename__ = "appointments"
    __table_args__ = (
        CheckConstraint(
            "appointment_status IN ('Scheduled', 'Confirmed', 'Cancelled', 'No Show', 'Rescheduled')",
            name="ck_appointments_status",
        ),
        CheckConstraint(
            "booking_source IN ('staff', 'public_link', 'ai_assistant', 'public_assistant')",
            name="ck_appointments_booking_source",
        ),
        CheckConstraint(
            "current_visit_status IS NULL OR current_visit_status IN "
            "('Arrived', 'In Consultation', 'Completed')",
            name="ck_appointments_visit_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    clinic_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clinics.id"), index=True, nullable=False
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patients.id"), index=True, nullable=False
    )
    doctor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("doctor_profiles.id"), index=True, nullable=False
    )
    room_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rooms.id"), nullable=True
    )
    scheduled_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    scheduled_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    reason_for_visit: Mapped[str | None] = mapped_column(String(512), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    appointment_status: Mapped[str] = mapped_column(String(32), default="Scheduled", nullable=False)
    current_visit_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    booking_source: Mapped[str] = mapped_column(String(32), default="staff", nullable=False)
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    series_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("appointment_series.id"), nullable=True, index=True
    )
    series_occurrence_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    service_fee_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("service_fees.id"), nullable=True, index=True
    )

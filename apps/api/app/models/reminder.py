import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, new_uuid

REMINDER_CHANNELS = ("email", "sms", "whatsapp")
REMINDER_TYPES = (
    "confirmation",
    "reminder_24h",
    "reminder_2h",
    "reschedule_notice",
    "cancellation_notice",
)
REMINDER_STATUSES = ("pending", "sent", "failed", "cancelled")
RECALL_SOURCES = ("follow_up_date", "chronic_condition_rule")
RECALL_STATUSES = ("pending", "contacted", "booked", "dismissed")


class Reminder(Base):
    __tablename__ = "reminders"
    __table_args__ = (UniqueConstraint("reply_token", name="uq_reminders_reply_token"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    appointment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("appointments.id"), index=True, nullable=False
    )
    clinic_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clinics.id"), index=True, nullable=False
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False
    )
    channel: Mapped[str] = mapped_column(String(16), nullable=False)
    reminder_type: Mapped[str] = mapped_column(String(32), nullable=False)
    scheduled_send_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), index=True, nullable=False
    )
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    provider_message_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    reply_token: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class PatientRecall(Base):
    __tablename__ = "patient_recalls"
    __table_args__ = (
        UniqueConstraint(
            "clinic_id",
            "patient_id",
            "source",
            "due_date",
            name="uq_patient_recalls_clinic_patient_source_due",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    clinic_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clinics.id"), index=True, nullable=False
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patients.id"), index=True, nullable=False
    )
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    source_soap_note_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("soap_notes.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

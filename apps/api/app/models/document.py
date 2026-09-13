import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, new_uuid

DOCUMENT_TYPES = (
    "medical_certificate",
    "referral_letter",
    "lab_request",
    "confinement_certificate",
    "custom",
)
DOCUMENT_STATUSES = ("draft", "issued")


class GeneratedDocument(Base, TimestampMixin):
    __tablename__ = "documents_generated"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    clinic_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clinics.id"), index=True, nullable=False
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patients.id"), index=True, nullable=False
    )
    appointment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("appointments.id"), nullable=True
    )
    template_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_templates.id"), nullable=False
    )
    document_type: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="draft", nullable=False)
    preview_content: Mapped[str] = mapped_column(Text, nullable=False)
    final_content_snapshot: Mapped[str | None] = mapped_column(Text, nullable=True)
    pdf_object_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    patient_file_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patient_files.id"), nullable=True
    )
    issued_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    issued_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    referral_recipient: Mapped[str | None] = mapped_column(String(255), nullable=True)
    referral_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    referral_outcome: Mapped[str | None] = mapped_column(Text, nullable=True)
    chart_share_token_hash: Mapped[str | None] = mapped_column(
        String(128), unique=True, nullable=True
    )
    chart_share_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

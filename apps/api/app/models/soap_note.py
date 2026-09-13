import uuid
from datetime import date, datetime
from typing import Any

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, new_uuid


class SoapNote(Base):
    """Append-only SOAP versions. Never UPDATE clinical fields on existing rows."""

    __tablename__ = "soap_notes"
    __table_args__ = (
        UniqueConstraint(
            "appointment_id", "version_number", name="uq_soap_notes_appointment_version"
        ),
        UniqueConstraint(
            "appointment_id", "client_draft_token", name="uq_soap_notes_appointment_draft_token"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    appointment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("appointments.id"), index=True, nullable=False
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False
    )
    doctor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("doctor_profiles.id"), nullable=False
    )
    clinic_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clinics.id"), index=True, nullable=False
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    subjective: Mapped[str | None] = mapped_column(Text, nullable=True)
    objective: Mapped[str | None] = mapped_column(Text, nullable=True)
    assessment: Mapped[str | None] = mapped_column(Text, nullable=True)
    plan: Mapped[str | None] = mapped_column(Text, nullable=True)
    diagnosis_primary: Mapped[str | None] = mapped_column(String(512), nullable=True)
    diagnosis_secondary: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    icd10_codes: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    follow_up_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    specialty_template_key: Mapped[str | None] = mapped_column(String(64), nullable=True)
    specialty_data: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    signed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    signature_image_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    client_draft_token: Mapped[str | None] = mapped_column(String(64), nullable=True)


class DocumentTemplate(Base):
    __tablename__ = "document_templates"
    __table_args__ = (
        UniqueConstraint("clinic_id", "template_key", name="uq_document_templates_clinic_key"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    clinic_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clinics.id"), index=True, nullable=True
    )
    template_key: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    template_type: Mapped[str] = mapped_column(String(32), default="soap", nullable=False)
    schema_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    body: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    body_template: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

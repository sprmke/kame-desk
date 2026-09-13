import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, new_uuid


class DrugReference(Base):
    __tablename__ = "drug_reference"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    generic_name: Mapped[str] = mapped_column(String(128), nullable=False)
    known_allergen_classes: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)
    interaction_with: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)


class Prescription(Base, TimestampMixin):
    __tablename__ = "prescriptions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patients.id"), index=True, nullable=False
    )
    doctor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("doctor_profiles.id"), nullable=False
    )
    clinic_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clinics.id"), index=True, nullable=False
    )
    appointment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("appointments.id"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(16), default="draft", nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    pdf_object_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    issued_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    voided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    void_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    override_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    conflict_flags: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB, nullable=True)
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )

    items: Mapped[list["PrescriptionItem"]] = relationship(
        back_populates="prescription",
        order_by="PrescriptionItem.sort_order",
        cascade="all, delete-orphan",
    )


class PrescriptionItem(Base):
    __tablename__ = "prescription_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    prescription_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("prescriptions.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    drug_name: Mapped[str] = mapped_column(String(256), nullable=False)
    generic_name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    dosage: Mapped[str | None] = mapped_column(String(128), nullable=True)
    form: Mapped[str | None] = mapped_column(String(64), nullable=True)
    frequency: Mapped[str | None] = mapped_column(String(128), nullable=True)
    duration: Mapped[str | None] = mapped_column(String(128), nullable=True)
    quantity: Mapped[str | None] = mapped_column(String(64), nullable=True)
    special_instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    prescription: Mapped["Prescription"] = relationship(back_populates="items")

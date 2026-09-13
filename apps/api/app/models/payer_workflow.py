import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, new_uuid

PAYER_TYPES = ("hmo", "philhealth", "self_pay", "other")
ELIGIBILITY_STATUSES = ("pending", "verified", "denied", "expired")
LOA_STATUSES = ("requested", "submitted", "approved", "denied")


class Payer(Base, TimestampMixin):
    """Clinic-managed directory of HMO/PhilHealth payer names used by claim/eligibility/LOA forms."""

    __tablename__ = "payers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    clinic_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clinics.id"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    payer_type: Mapped[str] = mapped_column(String(20), default="hmo", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class EligibilityCheck(Base, TimestampMixin):
    __tablename__ = "eligibility_checks"
    __table_args__ = (
        CheckConstraint(
            "payer_type IN ('hmo', 'philhealth', 'self_pay', 'other')",
            name="ck_eligibility_checks_payer_type",
        ),
        CheckConstraint(
            "status IN ('pending', 'verified', 'denied', 'expired')",
            name="ck_eligibility_checks_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    clinic_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clinics.id"), index=True, nullable=False
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patients.id"), index=True, nullable=False
    )
    payer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    payer_type: Mapped[str] = mapped_column(String(20), default="hmo", nullable=False)
    member_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    verified_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    checked_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class LoaRequest(Base, TimestampMixin):
    __tablename__ = "loa_requests"
    __table_args__ = (
        CheckConstraint(
            "status IN ('requested', 'submitted', 'approved', 'denied')",
            name="ck_loa_requests_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    clinic_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clinics.id"), index=True, nullable=False
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patients.id"), index=True, nullable=False
    )
    claim_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("insurance_claims.id"), nullable=True
    )
    hmo_name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="requested", nullable=False)
    reference_number: Mapped[str | None] = mapped_column(String(128), nullable=True)
    document_object_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    requested_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    decision_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

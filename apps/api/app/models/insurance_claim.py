import uuid
from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, new_uuid


class InsuranceClaim(Base, TimestampMixin):
    __tablename__ = "insurance_claims"
    __table_args__ = (
        CheckConstraint(
            "status IN ('draft', 'submitted', 'approved', 'denied', 'paid')",
            name="ck_insurance_claims_status",
        ),
        CheckConstraint(
            "payer_type IN ('hmo', 'philhealth', 'self_pay', 'other')",
            name="ck_insurance_claims_payer_type",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    clinic_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clinics.id"), index=True, nullable=False
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patients.id"), index=True, nullable=False
    )
    invoice_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("invoices.id"), nullable=True
    )
    provider: Mapped[str] = mapped_column(String(255), nullable=False)
    payer_type: Mapped[str] = mapped_column(String(20), default="hmo", nullable=False)
    member_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    claim_reference: Mapped[str | None] = mapped_column(String(128), nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="draft", nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    loa_request_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("loa_requests.id"), nullable=True
    )
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )

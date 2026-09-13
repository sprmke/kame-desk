import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.models.organization import Organization, OrganizationEnrolledClinic

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, new_uuid


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    email_verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    memberships: Mapped[list["ClinicMembership"]] = relationship(back_populates="user")


class Clinic(Base, TimestampMixin):
    __tablename__ = "clinics"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    logo_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    brand_color: Mapped[str | None] = mapped_column(String(7), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    contact_email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    timezone: Mapped[str] = mapped_column(String(64), default="Asia/Manila", nullable=False)
    license_info: Mapped[str | None] = mapped_column(Text, nullable=True)
    accreditation_info: Mapped[str | None] = mapped_column(Text, nullable=True)
    working_hours: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    holiday_dates: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    default_appointment_duration_minutes: Mapped[int] = mapped_column(
        Integer, default=30, nullable=False
    )
    onboarding_invite_skipped: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    onboarding_completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    public_booking_auto_confirm: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    reception_can_view_soap: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    receipt_numbering_config: Mapped[dict[str, object] | None] = mapped_column(JSONB, nullable=True)
    bir_compliance_config: Mapped[dict[str, object] | None] = mapped_column(JSONB, nullable=True)
    notification_preferences: Mapped[dict[str, object] | None] = mapped_column(JSONB, nullable=True)
    twilio_credentials_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    whatsapp_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    whatsapp_phone_number_id: Mapped[str | None] = mapped_column(
        String(64), index=True, nullable=True
    )
    whatsapp_credentials_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    recording_consent_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ai_assistant_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    assistant_disabled_tools: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    deletion_requested_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    plan_key: Mapped[str | None] = mapped_column(String(32), nullable=True)
    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), index=True, nullable=True
    )
    growth_settings: Mapped[dict[str, object] | None] = mapped_column(JSONB, nullable=True)

    organization: Mapped["Organization | None"] = relationship(back_populates="clinics")
    enrollment: Mapped["OrganizationEnrolledClinic | None"] = relationship(
        back_populates="clinic", uselist=False
    )
    memberships: Mapped[list["ClinicMembership"]] = relationship(back_populates="clinic")


class ClinicMembership(Base):
    __tablename__ = "clinic_memberships"
    __table_args__ = (
        UniqueConstraint("user_id", "clinic_id", name="uq_clinic_memberships_user_clinic"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), index=True, nullable=False
    )
    clinic_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clinics.id"), index=True, nullable=False
    )
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    in_app_notification_prefs: Mapped[dict[str, object] | None] = mapped_column(
        JSONB, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="memberships", foreign_keys=[user_id])
    clinic: Mapped["Clinic"] = relationship(back_populates="memberships", foreign_keys=[clinic_id])

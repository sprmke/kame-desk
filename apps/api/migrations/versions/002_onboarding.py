"""Extend clinics and add onboarding-related tables."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "002_onboarding"
down_revision: str | None = "001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("clinics", sa.Column("license_info", sa.Text(), nullable=True))
    op.add_column("clinics", sa.Column("accreditation_info", sa.Text(), nullable=True))
    op.add_column(
        "clinics",
        sa.Column("working_hours", postgresql.JSONB(), nullable=True),
    )
    op.add_column(
        "clinics",
        sa.Column("holiday_dates", postgresql.JSONB(), nullable=True),
    )
    op.add_column(
        "clinics",
        sa.Column(
            "default_appointment_duration_minutes",
            sa.Integer(),
            server_default="30",
            nullable=False,
        ),
    )
    op.add_column(
        "clinics",
        sa.Column(
            "onboarding_invite_skipped",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
    )
    op.add_column(
        "clinics", sa.Column("onboarding_completed_at", sa.DateTime(timezone=True), nullable=True)
    )

    op.create_table(
        "doctor_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False
        ),
        sa.Column(
            "clinic_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clinics.id"), nullable=False
        ),
        sa.Column("specialty", sa.String(128), nullable=True),
        sa.Column("prc_license_number", sa.String(64), nullable=True),
        sa.Column("signature_image_key", sa.String(512), nullable=True),
        sa.Column("photo_url", sa.String(2048), nullable=True),
        sa.Column("consultation_fee", sa.Numeric(12, 2), nullable=True),
        sa.Column("follow_up_fee", sa.Numeric(12, 2), nullable=True),
        sa.Column("default_appointment_duration_minutes", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("user_id", "clinic_id", name="uq_doctor_profiles_user_clinic"),
    )
    op.create_index("ix_doctor_profiles_clinic_id", "doctor_profiles", ["clinic_id"])

    op.create_table(
        "service_fees",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "clinic_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clinics.id"), nullable=False
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("category", sa.String(64), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_service_fees_clinic_id", "service_fees", ["clinic_id"])

    op.create_table(
        "staff_invitations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "clinic_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clinics.id"), nullable=False
        ),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("role", sa.String(32), nullable=False),
        sa.Column(
            "invited_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("token_hash", sa.String(128), nullable=False),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_staff_invitations_clinic_id", "staff_invitations", ["clinic_id"])
    op.create_index(
        "ix_staff_invitations_token_hash", "staff_invitations", ["token_hash"], unique=True
    )


def downgrade() -> None:
    op.drop_table("staff_invitations")
    op.drop_table("service_fees")
    op.drop_table("doctor_profiles")
    op.drop_column("clinics", "onboarding_completed_at")
    op.drop_column("clinics", "onboarding_invite_skipped")
    op.drop_column("clinics", "default_appointment_duration_minutes")
    op.drop_column("clinics", "holiday_dates")
    op.drop_column("clinics", "working_hours")
    op.drop_column("clinics", "accreditation_info")
    op.drop_column("clinics", "license_info")

"""Appointment types (duration on service fees), room FKs, and cancellation waitlist."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "023_scheduling_scale"
down_revision: str | None = "022_account_foundations"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "service_fees",
        sa.Column("duration_minutes", sa.Integer(), nullable=True),
    )
    op.add_column(
        "appointments",
        sa.Column(
            "service_fee_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("service_fees.id"),
            nullable=True,
        ),
    )
    op.create_index("ix_appointments_service_fee_id", "appointments", ["service_fee_id"])
    op.create_table(
        "appointment_waitlist",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "clinic_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("clinics.id"),
            nullable=False,
        ),
        sa.Column(
            "patient_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("patients.id"),
            nullable=False,
        ),
        sa.Column(
            "doctor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("doctor_profiles.id"),
            nullable=True,
        ),
        sa.Column("preferred_date", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="waiting"),
        sa.Column(
            "booked_appointment_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("appointments.id"),
            nullable=True,
        ),
        sa.Column(
            "created_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status IN ('waiting', 'booked', 'cancelled')",
            name="ck_appointment_waitlist_status",
        ),
    )
    op.create_index("ix_appointment_waitlist_clinic_id", "appointment_waitlist", ["clinic_id"])
    op.create_index("ix_appointment_waitlist_patient_id", "appointment_waitlist", ["patient_id"])


def downgrade() -> None:
    op.drop_index("ix_appointment_waitlist_patient_id", table_name="appointment_waitlist")
    op.drop_index("ix_appointment_waitlist_clinic_id", table_name="appointment_waitlist")
    op.drop_table("appointment_waitlist")
    op.drop_index("ix_appointments_service_fee_id", table_name="appointments")
    op.drop_column("appointments", "service_fee_id")
    op.drop_column("service_fees", "duration_minutes")

"""Clinic scheduling settings and public intake toggles."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "042_clinic_scheduling_settings"
down_revision: str | None = "041_doctor_specialty_key"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "clinics",
        sa.Column("slot_buffer_minutes", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "clinics",
        sa.Column("advance_booking_days", sa.Integer(), nullable=False, server_default="90"),
    )
    op.add_column(
        "clinics",
        sa.Column(
            "cancellation_notice_hours",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "clinics",
        sa.Column("public_intake_fields", postgresql.JSONB(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("clinics", "public_intake_fields")
    op.drop_column("clinics", "cancellation_notice_hours")
    op.drop_column("clinics", "advance_booking_days")
    op.drop_column("clinics", "slot_buffer_minutes")

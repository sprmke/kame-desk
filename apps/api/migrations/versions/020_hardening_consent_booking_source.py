"""Patient data consent timestamp and public_assistant booking source."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "020_hardening"
down_revision: str | None = "019_patient_assistant"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "patients",
        sa.Column("data_processing_consent_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.drop_constraint("ck_appointments_booking_source", "appointments", type_="check")
    op.create_check_constraint(
        "ck_appointments_booking_source",
        "appointments",
        "booking_source IN ('staff', 'public_link', 'ai_assistant', 'public_assistant')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_appointments_booking_source", "appointments", type_="check")
    op.create_check_constraint(
        "ck_appointments_booking_source",
        "appointments",
        "booking_source IN ('staff', 'public_link', 'ai_assistant')",
    )
    op.drop_column("patients", "data_processing_consent_at")

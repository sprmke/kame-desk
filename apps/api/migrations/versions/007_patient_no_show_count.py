"""Patients.no_show_count for later no-show prediction."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "007_patient_no_show_count"
down_revision: str | None = "006_appointment_series"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "patients",
        sa.Column("no_show_count", sa.Integer(), server_default="0", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("patients", "no_show_count")

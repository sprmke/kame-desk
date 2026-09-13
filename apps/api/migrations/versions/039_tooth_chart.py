"""Interactive odontogram / dental charting module (Phase 39)."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "039_tooth_chart"
down_revision: str | None = "038_organizations"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "tooth_chart_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "clinic_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clinics.id"), nullable=False
        ),
        sa.Column(
            "patient_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("patients.id"),
            nullable=False,
        ),
        sa.Column(
            "appointment_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("appointments.id"),
            nullable=True,
        ),
        sa.Column(
            "soap_note_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("soap_notes.id"),
            nullable=True,
        ),
        sa.Column("tooth_number", sa.Integer(), nullable=False),
        sa.Column("surface", sa.String(length=16), nullable=True),
        sa.Column("condition", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="existing"),
        sa.Column("procedure_code", sa.String(length=32), nullable=True),
        sa.Column(
            "invoice_line_item_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("invoice_line_items.id"),
            nullable=True,
        ),
        sa.Column("noted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_tooth_chart_entries_clinic_id", "tooth_chart_entries", ["clinic_id"])
    op.create_index("ix_tooth_chart_entries_patient_id", "tooth_chart_entries", ["patient_id"])


def downgrade() -> None:
    op.drop_index("ix_tooth_chart_entries_patient_id", table_name="tooth_chart_entries")
    op.drop_index("ix_tooth_chart_entries_clinic_id", table_name="tooth_chart_entries")
    op.drop_table("tooth_chart_entries")

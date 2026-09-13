"""Billing assist extraction audit rows."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "018_billing_extraction"
down_revision: str | None = "017_ai_assistant"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "billing_extraction_attempts",
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
            "actor_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("source_file_r2_key", sa.String(512), nullable=False),
        sa.Column("extracted_data", postgresql.JSONB(), nullable=False),
        sa.Column("confirmed", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_billing_extraction_attempts_patient_id",
        "billing_extraction_attempts",
        ["patient_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_billing_extraction_attempts_patient_id", table_name="billing_extraction_attempts"
    )
    op.drop_table("billing_extraction_attempts")

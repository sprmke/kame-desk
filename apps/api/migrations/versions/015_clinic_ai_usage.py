"""Per-clinic daily AI usage tracking."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "015_clinic_ai_usage"
down_revision: str | None = "014_activity_log_hardening"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "clinic_ai_usage",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "clinic_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("clinics.id"),
            nullable=False,
        ),
        sa.Column("usage_date", sa.Date(), nullable=False),
        sa.Column("request_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("token_count", sa.Integer(), server_default="0", nullable=False),
        sa.UniqueConstraint("clinic_id", "usage_date", name="uq_clinic_ai_usage_clinic_date"),
    )
    op.create_index("ix_clinic_ai_usage_clinic_id", "clinic_ai_usage", ["clinic_id"])


def downgrade() -> None:
    op.drop_index("ix_clinic_ai_usage_clinic_id", table_name="clinic_ai_usage")
    op.drop_table("clinic_ai_usage")

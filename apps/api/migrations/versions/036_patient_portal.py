"""Patient portal login tokens (Phase 37)."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "036_patient_portal"
down_revision: str | None = "035_in_app_notifications"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "patient_portal_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "patient_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("patients.id"),
            nullable=False,
        ),
        sa.Column(
            "clinic_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("clinics.id"),
            nullable=False,
        ),
        sa.Column("purpose", sa.String(length=32), nullable=False),
        sa.Column("token_hash", sa.String(length=128), nullable=False, unique=True),
        sa.Column("delivery_channel", sa.String(length=16), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_patient_portal_tokens_patient_id", "patient_portal_tokens", ["patient_id"])
    op.create_index("ix_patient_portal_tokens_clinic_id", "patient_portal_tokens", ["clinic_id"])


def downgrade() -> None:
    op.drop_index("ix_patient_portal_tokens_clinic_id", table_name="patient_portal_tokens")
    op.drop_index("ix_patient_portal_tokens_patient_id", table_name="patient_portal_tokens")
    op.drop_table("patient_portal_tokens")

"""Enforce uniqueness on clinics.whatsapp_phone_number_id (webhook routing key)."""

from collections.abc import Sequence

from alembic import op

revision: str = "033_whatsapp_phone_unique"
down_revision: str | None = "032_whatsapp_channel"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_index("ix_clinics_whatsapp_phone_number_id", table_name="clinics")
    op.create_index(
        "ix_clinics_whatsapp_phone_number_id",
        "clinics",
        ["whatsapp_phone_number_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_clinics_whatsapp_phone_number_id", table_name="clinics")
    op.create_index(
        "ix_clinics_whatsapp_phone_number_id",
        "clinics",
        ["whatsapp_phone_number_id"],
    )

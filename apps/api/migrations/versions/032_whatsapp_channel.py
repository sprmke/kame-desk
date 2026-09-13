"""WhatsApp messaging channel: clinic config columns."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "032_whatsapp_channel"
down_revision: str | None = "031_bir_compliance_depth"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "clinics",
        sa.Column("whatsapp_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "clinics",
        sa.Column("whatsapp_phone_number_id", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "clinics",
        sa.Column("whatsapp_credentials_encrypted", sa.Text(), nullable=True),
    )
    op.create_index(
        "ix_clinics_whatsapp_phone_number_id",
        "clinics",
        ["whatsapp_phone_number_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_clinics_whatsapp_phone_number_id", table_name="clinics")
    op.drop_column("clinics", "whatsapp_credentials_encrypted")
    op.drop_column("clinics", "whatsapp_phone_number_id")
    op.drop_column("clinics", "whatsapp_enabled")

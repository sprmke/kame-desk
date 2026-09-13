"""SOAP note client_draft_token for safe offline-queue retry (Phase 36)."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "034_soap_client_draft_token"
down_revision: str | None = "033_whatsapp_phone_unique"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "soap_notes",
        sa.Column("client_draft_token", sa.String(length=64), nullable=True),
    )
    op.create_unique_constraint(
        "uq_soap_notes_appointment_draft_token",
        "soap_notes",
        ["appointment_id", "client_draft_token"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_soap_notes_appointment_draft_token", "soap_notes", type_="unique")
    op.drop_column("soap_notes", "client_draft_token")

"""Clinic BIR compliance config (TIN, VAT status, PTU/CAS)."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "031_bir_compliance_depth"
down_revision: str | None = "030_ph_payer_workflow"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "clinics",
        sa.Column("bir_compliance_config", postgresql.JSONB(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("clinics", "bir_compliance_config")

"""Patient reminder opt-out."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "026_communications"
down_revision: str | None = "025_billing_integrity"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "patients",
        sa.Column(
            "reminders_opted_out",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )


def downgrade() -> None:
    op.drop_column("patients", "reminders_opted_out")

"""Visit summary generation_failed flag (honest AI failure)."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "021_visit_summary_fail"
down_revision: str | None = "020_hardening"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "visit_summaries",
        sa.Column(
            "generation_failed",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )


def downgrade() -> None:
    op.drop_column("visit_summaries", "generation_failed")

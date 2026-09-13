"""Clinic brand_color for letterhead/PDF accent."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "029_clinic_brand_color"
down_revision: str | None = "028_assistant_v2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "clinics",
        sa.Column("brand_color", sa.String(7), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("clinics", "brand_color")

"""Tooth chart: SET NULL on invoice line item delete, composite list index (Phase 39 hardening)."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "040_tooth_chart_fk_ondelete"
down_revision: str | None = "039_tooth_chart"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint(
        "tooth_chart_entries_invoice_line_item_id_fkey",
        "tooth_chart_entries",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "tooth_chart_entries_invoice_line_item_id_fkey",
        "tooth_chart_entries",
        "invoice_line_items",
        ["invoice_line_item_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.drop_index("ix_tooth_chart_entries_patient_id", table_name="tooth_chart_entries")
    op.create_index(
        "ix_tooth_chart_entries_patient_id_noted_at",
        "tooth_chart_entries",
        ["patient_id", sa.text("noted_at DESC")],
    )


def downgrade() -> None:
    op.drop_index("ix_tooth_chart_entries_patient_id_noted_at", table_name="tooth_chart_entries")
    op.create_index("ix_tooth_chart_entries_patient_id", "tooth_chart_entries", ["patient_id"])
    op.drop_constraint(
        "tooth_chart_entries_invoice_line_item_id_fkey",
        "tooth_chart_entries",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "tooth_chart_entries_invoice_line_item_id_fkey",
        "tooth_chart_entries",
        "invoice_line_items",
        ["invoice_line_item_id"],
        ["id"],
    )

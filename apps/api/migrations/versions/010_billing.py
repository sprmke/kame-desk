"""Invoices, line items, payments, receipt numbering config."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "010_billing"
down_revision: str | None = "009_prescriptions"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "clinics",
        sa.Column(
            "receipt_numbering_config",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text(
                '\'{"prefix": "OR-", "next_number": 1, "pad_width": 6}\'::jsonb'
            ),
            nullable=False,
        ),
    )

    op.create_table(
        "invoices",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("clinic_id", sa.UUID(), nullable=False),
        sa.Column("patient_id", sa.UUID(), nullable=False),
        sa.Column("appointment_id", sa.UUID(), nullable=True),
        sa.Column("invoice_number", sa.String(length=64), nullable=True),
        sa.Column("status", sa.String(length=20), server_default="draft", nullable=False),
        sa.Column(
            "subtotal", sa.Numeric(precision=12, scale=2), server_default="0", nullable=False
        ),
        sa.Column("total", sa.Numeric(precision=12, scale=2), server_default="0", nullable=False),
        sa.Column("void_reason", sa.Text(), nullable=True),
        sa.Column("pdf_object_key", sa.String(length=512), nullable=True),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("voided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by_user_id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"]),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"]),
        sa.ForeignKeyConstraint(["appointment_id"], ["appointments.id"]),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("clinic_id", "invoice_number", name="uq_invoices_clinic_number"),
    )
    op.create_index("ix_invoices_clinic_id", "invoices", ["clinic_id"])
    op.create_index("ix_invoices_patient_id", "invoices", ["patient_id"])

    op.create_table(
        "invoice_line_items",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("invoice_id", sa.UUID(), nullable=False),
        sa.Column("description", sa.String(length=512), nullable=False),
        sa.Column("category", sa.String(length=32), server_default="other", nullable=False),
        sa.Column(
            "quantity", sa.Numeric(precision=10, scale=2), server_default="1", nullable=False
        ),
        sa.Column("unit_price", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("hmo_covered_amount", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("hmo_claim_reference", sa.String(length=128), nullable=True),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.ForeignKeyConstraint(["invoice_id"], ["invoices.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_invoice_line_items_invoice_id", "invoice_line_items", ["invoice_id"])

    op.create_table(
        "payments",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("invoice_id", sa.UUID(), nullable=False),
        sa.Column("clinic_id", sa.UUID(), nullable=False),
        sa.Column("method", sa.String(length=32), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reference_number", sa.String(length=128), nullable=True),
        sa.Column("recorded_by_user_id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["invoice_id"], ["invoices.id"]),
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"]),
        sa.ForeignKeyConstraint(["recorded_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_payments_invoice_id", "payments", ["invoice_id"])
    op.create_index("ix_payments_clinic_id", "payments", ["clinic_id"])


def downgrade() -> None:
    op.drop_index("ix_payments_clinic_id", table_name="payments")
    op.drop_index("ix_payments_invoice_id", table_name="payments")
    op.drop_table("payments")
    op.drop_index("ix_invoice_line_items_invoice_id", table_name="invoice_line_items")
    op.drop_table("invoice_line_items")
    op.drop_index("ix_invoices_patient_id", table_name="invoices")
    op.drop_index("ix_invoices_clinic_id", table_name="invoices")
    op.drop_table("invoices")
    op.drop_column("clinics", "receipt_numbering_config")

"""Credit notes and insurance claims."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "025_billing_integrity"
down_revision: str | None = "024_clinical_safety"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "credit_notes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "clinic_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("clinics.id"),
            nullable=False,
        ),
        sa.Column(
            "invoice_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("invoices.id"),
            nullable=False,
        ),
        sa.Column(
            "patient_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("patients.id"),
            nullable=False,
        ),
        sa.Column("credit_number", sa.String(64), nullable=False),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column(
            "created_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint("kind IN ('refund', 'adjustment')", name="ck_credit_notes_kind"),
        sa.UniqueConstraint("clinic_id", "credit_number", name="uq_credit_notes_clinic_number"),
    )
    op.create_index("ix_credit_notes_clinic_id", "credit_notes", ["clinic_id"])
    op.create_index("ix_credit_notes_invoice_id", "credit_notes", ["invoice_id"])

    op.create_table(
        "insurance_claims",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "clinic_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("clinics.id"),
            nullable=False,
        ),
        sa.Column(
            "patient_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("patients.id"),
            nullable=False,
        ),
        sa.Column(
            "invoice_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("invoices.id"),
            nullable=True,
        ),
        sa.Column("provider", sa.String(255), nullable=False),
        sa.Column("member_id", sa.String(128), nullable=True),
        sa.Column("claim_reference", sa.String(128), nullable=True),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint(
            "status IN ('draft', 'submitted', 'approved', 'denied', 'paid')",
            name="ck_insurance_claims_status",
        ),
    )
    op.create_index("ix_insurance_claims_clinic_id", "insurance_claims", ["clinic_id"])
    op.create_index("ix_insurance_claims_patient_id", "insurance_claims", ["patient_id"])
    op.create_index("ix_insurance_claims_status", "insurance_claims", ["status"])


def downgrade() -> None:
    op.drop_index("ix_insurance_claims_status", table_name="insurance_claims")
    op.drop_index("ix_insurance_claims_patient_id", table_name="insurance_claims")
    op.drop_index("ix_insurance_claims_clinic_id", table_name="insurance_claims")
    op.drop_table("insurance_claims")
    op.drop_index("ix_credit_notes_invoice_id", table_name="credit_notes")
    op.drop_index("ix_credit_notes_clinic_id", table_name="credit_notes")
    op.drop_table("credit_notes")

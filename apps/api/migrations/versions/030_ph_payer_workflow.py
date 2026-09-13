"""PH payer workflow: payer directory, eligibility checks, LOA requests."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "030_ph_payer_workflow"
down_revision: str | None = "029_clinic_brand_color"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "payers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "clinic_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("clinics.id"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("payer_type", sa.String(20), nullable=False, server_default="hmo"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
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
    )
    op.create_index("ix_payers_clinic_id", "payers", ["clinic_id"])

    op.create_table(
        "eligibility_checks",
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
        sa.Column("payer_name", sa.String(255), nullable=False),
        sa.Column("payer_type", sa.String(20), nullable=False, server_default="hmo"),
        sa.Column("member_id", sa.String(128), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("verified_amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "checked_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("checked_at", sa.DateTime(timezone=True), nullable=False),
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
            "payer_type IN ('hmo', 'philhealth', 'self_pay', 'other')",
            name="ck_eligibility_checks_payer_type",
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'verified', 'denied', 'expired')",
            name="ck_eligibility_checks_status",
        ),
    )
    op.create_index("ix_eligibility_checks_clinic_id", "eligibility_checks", ["clinic_id"])
    op.create_index("ix_eligibility_checks_patient_id", "eligibility_checks", ["patient_id"])

    op.create_table(
        "loa_requests",
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
            "claim_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("insurance_claims.id"),
            nullable=True,
        ),
        sa.Column("hmo_name", sa.String(255), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="requested"),
        sa.Column("reference_number", sa.String(128), nullable=True),
        sa.Column("document_object_key", sa.String(512), nullable=True),
        sa.Column(
            "requested_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("decision_notes", sa.Text(), nullable=True),
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
            "status IN ('requested', 'submitted', 'approved', 'denied')",
            name="ck_loa_requests_status",
        ),
    )
    op.create_index("ix_loa_requests_clinic_id", "loa_requests", ["clinic_id"])
    op.create_index("ix_loa_requests_patient_id", "loa_requests", ["patient_id"])

    op.add_column(
        "insurance_claims",
        sa.Column("payer_type", sa.String(20), nullable=False, server_default="hmo"),
    )
    op.add_column(
        "insurance_claims",
        sa.Column(
            "loa_request_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("loa_requests.id"),
            nullable=True,
        ),
    )
    op.create_check_constraint(
        "ck_insurance_claims_payer_type",
        "insurance_claims",
        "payer_type IN ('hmo', 'philhealth', 'self_pay', 'other')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_insurance_claims_payer_type", "insurance_claims", type_="check")
    op.drop_column("insurance_claims", "loa_request_id")
    op.drop_column("insurance_claims", "payer_type")
    op.drop_table("loa_requests")
    op.drop_table("eligibility_checks")
    op.drop_table("payers")

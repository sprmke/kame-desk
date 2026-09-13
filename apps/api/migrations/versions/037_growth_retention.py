"""Growth & retention differentiators (Phase 38)."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "037_growth_retention"
down_revision: str | None = "036_patient_portal"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("clinics", sa.Column("growth_settings", postgresql.JSONB(), nullable=True))
    op.add_column("invoices", sa.Column("financing_status", sa.String(length=20), nullable=True))
    op.add_column(
        "documents_generated",
        sa.Column("chart_share_token_hash", sa.String(length=128), nullable=True),
    )
    op.create_unique_constraint(
        "uq_documents_generated_chart_share_token_hash",
        "documents_generated",
        ["chart_share_token_hash"],
    )
    op.add_column(
        "documents_generated",
        sa.Column("chart_share_expires_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "patient_survey_responses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "clinic_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clinics.id"), nullable=False
        ),
        sa.Column(
            "patient_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("patients.id"),
            nullable=False,
        ),
        sa.Column(
            "visit_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("appointments.id"),
            nullable=False,
        ),
        sa.Column("reply_token", sa.String(length=64), nullable=False, unique=True),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("responded_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_patient_survey_responses_clinic_id", "patient_survey_responses", ["clinic_id"]
    )
    op.create_index(
        "ix_patient_survey_responses_patient_id", "patient_survey_responses", ["patient_id"]
    )

    op.create_table(
        "membership_plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "clinic_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clinics.id"), nullable=False
        ),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("price", sa.Numeric(12, 2), nullable=False),
        sa.Column("billing_interval", sa.String(length=16), nullable=False),
        sa.Column("included_services", postgresql.JSONB(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_membership_plans_clinic_id", "membership_plans", ["clinic_id"])

    op.create_table(
        "patient_memberships",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "clinic_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clinics.id"), nullable=False
        ),
        sa.Column(
            "patient_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("patients.id"),
            nullable=False,
        ),
        sa.Column(
            "plan_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("membership_plans.id"),
            nullable=False,
        ),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="active"),
        sa.Column("started_at", sa.Date(), nullable=False),
        sa.Column("current_period_end", sa.Date(), nullable=False),
        sa.Column("usage_this_period", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_patient_memberships_clinic_id", "patient_memberships", ["clinic_id"])
    op.create_index("ix_patient_memberships_patient_id", "patient_memberships", ["patient_id"])


def downgrade() -> None:
    op.drop_index("ix_patient_memberships_patient_id", table_name="patient_memberships")
    op.drop_index("ix_patient_memberships_clinic_id", table_name="patient_memberships")
    op.drop_table("patient_memberships")

    op.drop_index("ix_membership_plans_clinic_id", table_name="membership_plans")
    op.drop_table("membership_plans")

    op.drop_index("ix_patient_survey_responses_patient_id", table_name="patient_survey_responses")
    op.drop_index("ix_patient_survey_responses_clinic_id", table_name="patient_survey_responses")
    op.drop_table("patient_survey_responses")

    op.drop_column("documents_generated", "chart_share_expires_at")
    op.drop_constraint(
        "uq_documents_generated_chart_share_token_hash",
        "documents_generated",
        type_="unique",
    )
    op.drop_column("documents_generated", "chart_share_token_hash")
    op.drop_column("invoices", "financing_status")
    op.drop_column("clinics", "growth_settings")

"""SOAP notes, document templates, clinic reception SOAP access."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "008_soap_notes"
down_revision: str | None = "007_patient_no_show_count"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "clinics",
        sa.Column(
            "reception_can_view_soap",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
    )

    op.create_table(
        "document_templates",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("clinic_id", sa.UUID(), nullable=True),
        sa.Column("template_key", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("template_type", sa.String(length=32), server_default="soap", nullable=False),
        sa.Column("schema_version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("body", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("clinic_id", "template_key", name="uq_document_templates_clinic_key"),
    )
    op.create_index("ix_document_templates_clinic_id", "document_templates", ["clinic_id"])

    op.create_table(
        "soap_notes",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("appointment_id", sa.UUID(), nullable=False),
        sa.Column("patient_id", sa.UUID(), nullable=False),
        sa.Column("doctor_id", sa.UUID(), nullable=False),
        sa.Column("clinic_id", sa.UUID(), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("subjective", sa.Text(), nullable=True),
        sa.Column("objective", sa.Text(), nullable=True),
        sa.Column("assessment", sa.Text(), nullable=True),
        sa.Column("plan", sa.Text(), nullable=True),
        sa.Column("diagnosis_primary", sa.String(length=512), nullable=True),
        sa.Column("diagnosis_secondary", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("icd10_codes", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("follow_up_date", sa.Date(), nullable=True),
        sa.Column("specialty_template_key", sa.String(length=64), nullable=True),
        sa.Column("specialty_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("signed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("signature_image_url", sa.String(length=2048), nullable=True),
        sa.Column("created_by_user_id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["appointment_id"], ["appointments.id"]),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"]),
        sa.ForeignKeyConstraint(["doctor_id"], ["doctor_profiles.id"]),
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"]),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "appointment_id", "version_number", name="uq_soap_notes_appointment_version"
        ),
    )
    op.create_index("ix_soap_notes_appointment_id", "soap_notes", ["appointment_id"])
    op.create_index("ix_soap_notes_clinic_id", "soap_notes", ["clinic_id"])


def downgrade() -> None:
    op.drop_index("ix_soap_notes_clinic_id", table_name="soap_notes")
    op.drop_index("ix_soap_notes_appointment_id", table_name="soap_notes")
    op.drop_table("soap_notes")
    op.drop_index("ix_document_templates_clinic_id", table_name="document_templates")
    op.drop_table("document_templates")
    op.drop_column("clinics", "reception_can_view_soap")

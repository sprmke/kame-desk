"""Generated clinical documents and letter-template columns."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "011_documents_generated"
down_revision: str | None = "010_billing"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "document_templates",
        sa.Column("body_template", sa.Text(), nullable=True),
    )
    op.add_column(
        "document_templates",
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
    )

    op.create_table(
        "documents_generated",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("clinic_id", sa.UUID(), nullable=False),
        sa.Column("patient_id", sa.UUID(), nullable=False),
        sa.Column("appointment_id", sa.UUID(), nullable=True),
        sa.Column("template_id", sa.UUID(), nullable=False),
        sa.Column("document_type", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="draft", nullable=False),
        sa.Column("preview_content", sa.Text(), nullable=False),
        sa.Column("final_content_snapshot", sa.Text(), nullable=True),
        sa.Column("pdf_object_key", sa.String(length=512), nullable=True),
        sa.Column("patient_file_id", sa.UUID(), nullable=True),
        sa.Column("issued_by_user_id", sa.UUID(), nullable=True),
        sa.Column("created_by_user_id", sa.UUID(), nullable=False),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.ForeignKeyConstraint(["template_id"], ["document_templates.id"]),
        sa.ForeignKeyConstraint(["patient_file_id"], ["patient_files.id"]),
        sa.ForeignKeyConstraint(["issued_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_documents_generated_clinic_id", "documents_generated", ["clinic_id"])
    op.create_index("ix_documents_generated_patient_id", "documents_generated", ["patient_id"])


def downgrade() -> None:
    op.drop_index("ix_documents_generated_patient_id", table_name="documents_generated")
    op.drop_index("ix_documents_generated_clinic_id", table_name="documents_generated")
    op.drop_table("documents_generated")
    op.drop_column("document_templates", "is_active")
    op.drop_column("document_templates", "body_template")

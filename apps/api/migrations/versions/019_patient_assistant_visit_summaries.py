"""Patient assistant conversations and visit summaries."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "019_patient_assistant"
down_revision: str | None = "018_billing_extraction"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "patient_assistant_conversations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "clinic_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("clinics.id"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_patient_assistant_conversations_clinic_id",
        "patient_assistant_conversations",
        ["clinic_id"],
    )

    op.create_table(
        "patient_assistant_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "conversation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("patient_assistant_conversations.id"),
            nullable=False,
        ),
        sa.Column("role", sa.String(16), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_patient_assistant_messages_conversation_id",
        "patient_assistant_messages",
        ["conversation_id"],
    )

    op.create_table(
        "visit_summaries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "clinic_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("clinics.id"),
            nullable=False,
        ),
        sa.Column(
            "appointment_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("appointments.id"),
            nullable=False,
        ),
        sa.Column("generated_text", sa.Text(), nullable=False),
        sa.Column("edited_text", sa.Text(), nullable=True),
        sa.Column("status", sa.String(16), nullable=False, server_default="draft"),
        sa.Column(
            "reviewed_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("appointment_id", name="uq_visit_summaries_appointment_id"),
    )
    op.create_index("ix_visit_summaries_clinic_id", "visit_summaries", ["clinic_id"])


def downgrade() -> None:
    op.drop_index("ix_visit_summaries_clinic_id", table_name="visit_summaries")
    op.drop_table("visit_summaries")
    op.drop_index(
        "ix_patient_assistant_messages_conversation_id",
        table_name="patient_assistant_messages",
    )
    op.drop_table("patient_assistant_messages")
    op.drop_index(
        "ix_patient_assistant_conversations_clinic_id",
        table_name="patient_assistant_conversations",
    )
    op.drop_table("patient_assistant_conversations")

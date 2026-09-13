"""Transcription recordings, SOAP embeddings (pgvector), recording consent."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "016_transcription_embeddings"
down_revision: str | None = "015_clinic_ai_usage"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

EMBEDDING_DIMENSIONS = 256


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.add_column(
        "clinics",
        sa.Column(
            "recording_consent_enabled",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
    )

    op.create_table(
        "consultation_recordings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "appointment_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("appointments.id"),
            nullable=False,
        ),
        sa.Column(
            "clinic_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("clinics.id"),
            nullable=False,
        ),
        sa.Column("r2_key", sa.String(512), nullable=False),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column(
            "transcription_status",
            sa.String(32),
            server_default="pending",
            nullable=False,
        ),
        sa.Column("transcript_text", sa.Text(), nullable=True),
        sa.Column(
            "created_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("processing_started_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_consultation_recordings_appointment_id",
        "consultation_recordings",
        ["appointment_id"],
    )
    op.create_index(
        "ix_consultation_recordings_clinic_id",
        "consultation_recordings",
        ["clinic_id"],
    )

    op.execute(
        f"""
        CREATE TABLE soap_note_embeddings (
            id UUID PRIMARY KEY,
            soap_note_id UUID NOT NULL UNIQUE REFERENCES soap_notes(id),
            clinic_id UUID NOT NULL REFERENCES clinics(id),
            embedding vector({EMBEDDING_DIMENSIONS}) NOT NULL,
            embedding_model_version VARCHAR(64) NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.create_index("ix_soap_note_embeddings_clinic_id", "soap_note_embeddings", ["clinic_id"])


def downgrade() -> None:
    op.drop_index("ix_soap_note_embeddings_clinic_id", table_name="soap_note_embeddings")
    op.drop_table("soap_note_embeddings")
    op.drop_index("ix_consultation_recordings_clinic_id", table_name="consultation_recordings")
    op.drop_index(
        "ix_consultation_recordings_appointment_id",
        table_name="consultation_recordings",
    )
    op.drop_table("consultation_recordings")
    op.drop_column("clinics", "recording_consent_enabled")

"""Reminders, patient recalls, clinic notification preferences."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "012_reminders_recalls"
down_revision: str | None = "011_documents_generated"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "clinics",
        sa.Column(
            "notification_preferences",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text(
                '\'{"email_enabled": true, "sms_enabled": false, '
                '"confirmation_enabled": true, "reminder_24h_enabled": true, '
                '"reminder_2h_enabled": false, "sender_name": null, '
                '"chronic_condition_rules": []}\'::jsonb'
            ),
            nullable=False,
        ),
    )
    op.add_column(
        "clinics",
        sa.Column("twilio_credentials_encrypted", sa.Text(), nullable=True),
    )

    op.create_table(
        "reminders",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("appointment_id", sa.UUID(), nullable=False),
        sa.Column("clinic_id", sa.UUID(), nullable=False),
        sa.Column("patient_id", sa.UUID(), nullable=False),
        sa.Column("channel", sa.String(length=16), nullable=False),
        sa.Column("reminder_type", sa.String(length=32), nullable=False),
        sa.Column("scheduled_send_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=20), server_default="pending", nullable=False),
        sa.Column("provider_message_id", sa.String(length=128), nullable=True),
        sa.Column("reply_token", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["appointment_id"], ["appointments.id"]),
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"]),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("reply_token", name="uq_reminders_reply_token"),
    )
    op.create_index("ix_reminders_appointment_id", "reminders", ["appointment_id"])
    op.create_index("ix_reminders_clinic_id", "reminders", ["clinic_id"])
    op.create_index("ix_reminders_scheduled_send_at", "reminders", ["scheduled_send_at"])

    op.create_table(
        "patient_recalls",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("clinic_id", sa.UUID(), nullable=False),
        sa.Column("patient_id", sa.UUID(), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="pending", nullable=False),
        sa.Column("source_soap_note_id", sa.UUID(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"]),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"]),
        sa.ForeignKeyConstraint(["source_soap_note_id"], ["soap_notes.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "clinic_id",
            "patient_id",
            "source",
            "due_date",
            name="uq_patient_recalls_clinic_patient_source_due",
        ),
    )
    op.create_index("ix_patient_recalls_clinic_id", "patient_recalls", ["clinic_id"])
    op.create_index("ix_patient_recalls_patient_id", "patient_recalls", ["patient_id"])


def downgrade() -> None:
    op.drop_index("ix_patient_recalls_patient_id", table_name="patient_recalls")
    op.drop_index("ix_patient_recalls_clinic_id", table_name="patient_recalls")
    op.drop_table("patient_recalls")
    op.drop_index("ix_reminders_scheduled_send_at", table_name="reminders")
    op.drop_index("ix_reminders_clinic_id", table_name="reminders")
    op.drop_index("ix_reminders_appointment_id", table_name="reminders")
    op.drop_table("reminders")
    op.drop_column("clinics", "twilio_credentials_encrypted")
    op.drop_column("clinics", "notification_preferences")

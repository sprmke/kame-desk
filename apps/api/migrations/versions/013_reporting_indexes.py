"""Reporting indexes for clinic-scoped aggregates."""

from collections.abc import Sequence

from alembic import op

revision: str = "013_reporting_indexes"
down_revision: str | None = "012_reminders_recalls"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "ix_appointments_clinic_scheduled_start",
        "appointments",
        ["clinic_id", "scheduled_start"],
        unique=False,
    )
    op.create_index(
        "ix_patients_clinic_created_at",
        "patients",
        ["clinic_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_payments_clinic_paid_at",
        "payments",
        ["clinic_id", "paid_at"],
        unique=False,
    )
    op.create_index(
        "ix_soap_notes_clinic_signed_at",
        "soap_notes",
        ["clinic_id", "signed_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_soap_notes_clinic_signed_at", table_name="soap_notes")
    op.drop_index("ix_payments_clinic_paid_at", table_name="payments")
    op.drop_index("ix_patients_clinic_created_at", table_name="patients")
    op.drop_index("ix_appointments_clinic_scheduled_start", table_name="appointments")

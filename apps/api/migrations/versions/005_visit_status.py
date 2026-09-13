"""Visit status events and appointments.current_visit_status."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "005_visit_status"
down_revision: str | None = "004_public_booking_calendar"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

VISIT_STATUSES = ("Arrived", "In Consultation", "Completed")


def upgrade() -> None:
    op.add_column(
        "appointments",
        sa.Column("current_visit_status", sa.String(length=32), nullable=True),
    )
    op.create_check_constraint(
        "ck_appointments_visit_status",
        "appointments",
        "current_visit_status IS NULL OR current_visit_status IN "
        "('Arrived', 'In Consultation', 'Completed')",
    )

    op.create_table(
        "visit_status_events",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("appointment_id", sa.UUID(), nullable=False),
        sa.Column("clinic_id", sa.UUID(), nullable=False),
        sa.Column("visit_status", sa.String(length=32), nullable=False),
        sa.Column(
            "changed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("changed_by_user_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["appointment_id"], ["appointments.id"]),
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"]),
        sa.ForeignKeyConstraint(["changed_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "visit_status IN ('Arrived', 'In Consultation', 'Completed')",
            name="ck_visit_status_events_status",
        ),
    )
    op.create_index(
        "ix_visit_status_events_appointment_id",
        "visit_status_events",
        ["appointment_id"],
    )
    op.create_index("ix_visit_status_events_clinic_id", "visit_status_events", ["clinic_id"])


def downgrade() -> None:
    op.drop_index("ix_visit_status_events_clinic_id", table_name="visit_status_events")
    op.drop_index("ix_visit_status_events_appointment_id", table_name="visit_status_events")
    op.drop_table("visit_status_events")
    op.drop_constraint("ck_appointments_visit_status", "appointments", type_="check")
    op.drop_column("appointments", "current_visit_status")

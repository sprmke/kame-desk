"""Appointment series and recurring linkage."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "006_appointment_series"
down_revision: str | None = "005_visit_status"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "appointment_series",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("clinic_id", sa.UUID(), nullable=False),
        sa.Column("doctor_id", sa.UUID(), nullable=False),
        sa.Column("patient_id", sa.UUID(), nullable=False),
        sa.Column("rrule_string", sa.String(length=512), nullable=False),
        sa.Column("series_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("series_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_minutes", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("reason_for_visit", sa.String(length=512), nullable=True),
        sa.Column("created_by_user_id", sa.UUID(), nullable=False),
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
        sa.ForeignKeyConstraint(["doctor_id"], ["doctor_profiles.id"]),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"]),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_appointment_series_clinic_id", "appointment_series", ["clinic_id"])

    op.add_column("appointments", sa.Column("series_id", sa.UUID(), nullable=True))
    op.add_column(
        "appointments",
        sa.Column("series_occurrence_index", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_appointments_series_id",
        "appointments",
        "appointment_series",
        ["series_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_appointments_series_id", "appointments", ["series_id"])
    op.create_index(
        "uq_appointments_series_occurrence",
        "appointments",
        ["series_id", "series_occurrence_index"],
        unique=True,
        postgresql_where=sa.text("series_id IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_appointments_series_occurrence", table_name="appointments")
    op.drop_index("ix_appointments_series_id", table_name="appointments")
    op.drop_constraint("fk_appointments_series_id", "appointments", type_="foreignkey")
    op.drop_column("appointments", "series_occurrence_index")
    op.drop_column("appointments", "series_id")
    op.drop_index("ix_appointment_series_clinic_id", table_name="appointment_series")
    op.drop_table("appointment_series")

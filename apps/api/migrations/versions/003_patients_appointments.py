"""Patients, appointments, rooms, and double-booking exclusion constraints."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "003_patients_appointments"
down_revision: str | None = "002_onboarding"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

APPOINTMENT_TERMINAL = ("Cancelled", "No Show", "Rescheduled")


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    op.create_table(
        "patients",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "clinic_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clinics.id"), nullable=False
        ),
        sa.Column("patient_number", sa.Integer(), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("birthdate", sa.Date(), nullable=True),
        sa.Column("sex", sa.String(16), nullable=True),
        sa.Column("civil_status", sa.String(32), nullable=True),
        sa.Column("occupation", sa.String(128), nullable=True),
        sa.Column("contact_number", sa.String(50), nullable=True),
        sa.Column("email", sa.String(320), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("emergency_contact", postgresql.JSONB(), nullable=True),
        sa.Column("insurance_info", postgresql.JSONB(), nullable=True),
        sa.Column("is_archived", sa.Boolean(), server_default=sa.text("false"), nullable=False),
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
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("clinic_id", "patient_number", name="uq_patients_clinic_number"),
    )
    op.create_index("ix_patients_clinic_id", "patients", ["clinic_id"])
    op.create_index(
        "ix_patients_full_name_trgm",
        "patients",
        ["full_name"],
        postgresql_using="gin",
        postgresql_ops={"full_name": "gin_trgm_ops"},
    )
    op.execute(
        "CREATE INDEX ix_patients_contact_trgm ON patients USING gin (contact_number gin_trgm_ops)"
    )

    op.create_table(
        "patient_medical_info",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "patient_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("patients.id"),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "clinic_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clinics.id"), nullable=False
        ),
        sa.Column(
            "allergies_reviewed", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
        sa.Column(
            "allergies", postgresql.JSONB(), server_default=sa.text("'[]'::jsonb"), nullable=False
        ),
        sa.Column("medical_history", sa.Text(), nullable=True),
        sa.Column("family_history", sa.Text(), nullable=True),
        sa.Column("surgical_history", sa.Text(), nullable=True),
        sa.Column(
            "current_medications",
            postgresql.JSONB(),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "chronic_conditions",
            postgresql.JSONB(),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "vaccination_history",
            postgresql.JSONB(),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column("clinical_notes", sa.Text(), nullable=True),
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
    )
    op.create_index("ix_patient_medical_info_clinic_id", "patient_medical_info", ["clinic_id"])

    op.create_table(
        "patient_vitals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "patient_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("patients.id"),
            nullable=False,
        ),
        sa.Column(
            "clinic_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clinics.id"), nullable=False
        ),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("height_cm", sa.Numeric(5, 2), nullable=True),
        sa.Column("weight_kg", sa.Numeric(5, 2), nullable=True),
        sa.Column("bmi", sa.Numeric(5, 2), nullable=True),
        sa.Column("blood_pressure", sa.String(16), nullable=True),
        sa.Column("temperature_c", sa.Numeric(4, 2), nullable=True),
        sa.Column("heart_rate", sa.Integer(), nullable=True),
        sa.Column("respiratory_rate", sa.Integer(), nullable=True),
        sa.Column("spo2", sa.Integer(), nullable=True),
        sa.Column(
            "recorded_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("visit_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_patient_vitals_patient_id", "patient_vitals", ["patient_id"])
    op.create_index("ix_patient_vitals_clinic_id", "patient_vitals", ["clinic_id"])

    op.create_table(
        "patient_files",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "patient_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("patients.id"),
            nullable=False,
        ),
        sa.Column(
            "clinic_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clinics.id"), nullable=False
        ),
        sa.Column("r2_key", sa.String(512), nullable=False),
        sa.Column("file_type", sa.String(32), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "uploaded_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("visit_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "uploaded_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_patient_files_patient_id", "patient_files", ["patient_id"])
    op.create_index("ix_patient_files_clinic_id", "patient_files", ["clinic_id"])

    op.create_table(
        "rooms",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "clinic_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clinics.id"), nullable=False
        ),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("clinic_id", "name", name="uq_rooms_clinic_name"),
    )
    op.create_index("ix_rooms_clinic_id", "rooms", ["clinic_id"])

    op.create_table(
        "appointments",
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
            "doctor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("doctor_profiles.id"),
            nullable=False,
        ),
        sa.Column(
            "room_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("rooms.id"), nullable=True
        ),
        sa.Column("scheduled_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("scheduled_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reason_for_visit", sa.String(512), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("appointment_status", sa.String(32), server_default="Scheduled", nullable=False),
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
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "appointment_status IN ('Scheduled', 'Confirmed', 'Cancelled', 'No Show', 'Rescheduled')",
            name="ck_appointments_status",
        ),
    )
    op.create_index("ix_appointments_clinic_id", "appointments", ["clinic_id"])
    op.create_index("ix_appointments_doctor_id", "appointments", ["doctor_id"])
    op.create_index("ix_appointments_patient_id", "appointments", ["patient_id"])
    op.create_index("ix_appointments_scheduled_start", "appointments", ["scheduled_start"])

    terminal = "', '".join(APPOINTMENT_TERMINAL)
    op.execute(
        f"""
        ALTER TABLE appointments ADD CONSTRAINT appointments_doctor_no_overlap
        EXCLUDE USING gist (
            doctor_id WITH =,
            tstzrange(scheduled_start, scheduled_end, '[)') WITH &&
        ) WHERE (appointment_status NOT IN ('{terminal}'))
        """
    )
    op.execute(
        f"""
        ALTER TABLE appointments ADD CONSTRAINT appointments_room_no_overlap
        EXCLUDE USING gist (
            room_id WITH =,
            tstzrange(scheduled_start, scheduled_end, '[)') WITH &&
        ) WHERE (room_id IS NOT NULL AND appointment_status NOT IN ('{terminal}'))
        """
    )


def downgrade() -> None:
    op.execute("ALTER TABLE appointments DROP CONSTRAINT IF EXISTS appointments_room_no_overlap")
    op.execute("ALTER TABLE appointments DROP CONSTRAINT IF EXISTS appointments_doctor_no_overlap")
    op.drop_table("appointments")
    op.drop_table("rooms")
    op.drop_table("patient_files")
    op.drop_table("patient_vitals")
    op.drop_table("patient_medical_info")
    op.execute("DROP INDEX IF EXISTS ix_patients_contact_trgm")
    op.drop_index("ix_patients_full_name_trgm", table_name="patients")
    op.drop_table("patients")

"""Curated drug expansion, clinical orders, and referral tracking columns."""

import uuid
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "024_clinical_safety"
down_revision: str | None = "023_scheduling_scale"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

EXTRA_DRUGS = [
    ("Cefalexin", "cefalexin", ["cephalosporin"], ["warfarin"]),
    ("Ciprofloxacin", "ciprofloxacin", [], ["warfarin", "theophylline"]),
    ("Azithromycin", "azithromycin", [], ["warfarin"]),
    ("Clindamycin", "clindamycin", [], []),
    ("Cotrimoxazole", "sulfamethoxazole-trimethoprim", ["sulfa"], ["warfarin"]),
    ("Metronidazole", "metronidazole", [], ["warfarin", "alcohol"]),
    ("Doxycycline", "doxycycline", [], []),
    ("Omeprazole", "omeprazole", [], ["clopidogrel", "warfarin"]),
    ("Amlodipine", "amlodipine", [], []),
    ("Simvastatin", "simvastatin", [], ["clarithromycin"]),
    ("Atorvastatin", "atorvastatin", [], ["clarithromycin"]),
    ("Losartan HCTZ", "losartan-hctz", [], ["potassium supplements"]),
    ("Gliclazide", "gliclazide", ["sulfonylurea"], []),
    ("Insulin Regular", "insulin", [], []),
    ("Salbutamol", "salbutamol", [], []),
    ("Prednisone", "prednisone", [], ["nsaid"]),
    ("Cetirizine", "cetirizine", [], []),
    ("Loratadine", "loratadine", [], []),
    ("Mefenamic Acid", "mefenamic acid", ["nsaid"], ["warfarin"]),
    ("Tramadol", "tramadol", [], ["ssri"]),
    ("Sertraline", "sertraline", ["ssri"], ["tramadol", "warfarin"]),
    ("Clopidogrel", "clopidogrel", [], ["omeprazole"]),
    ("Theophylline", "theophylline", [], ["ciprofloxacin"]),
    ("Clarithromycin", "clarithromycin", [], ["simvastatin", "atorvastatin"]),
]


def _pg_varchar_array(items: list[str]) -> str:
    if not items:
        return "ARRAY[]::varchar[]"
    inner = ",".join("'" + item.replace("'", "''") + "'" for item in items)
    return f"ARRAY[{inner}]::varchar[]"


def upgrade() -> None:
    conn = op.get_bind()
    for name, generic, allergens, interactions in EXTRA_DRUGS:
        exists = conn.execute(
            sa.text("SELECT 1 FROM drug_reference WHERE lower(name) = lower(:n)"),
            {"n": name},
        ).scalar()
        if exists:
            continue
        conn.execute(
            sa.text(
                "INSERT INTO drug_reference (id, name, generic_name, known_allergen_classes, interaction_with) "
                f"VALUES ('{uuid.uuid4()}', :name, :generic, {_pg_varchar_array(allergens)}, "
                f"{_pg_varchar_array(interactions)})"
            ),
            {"name": name, "generic": generic},
        )

    op.add_column(
        "documents_generated",
        sa.Column("referral_recipient", sa.String(255), nullable=True),
    )
    op.add_column(
        "documents_generated",
        sa.Column("referral_status", sa.String(32), nullable=True),
    )
    op.add_column(
        "documents_generated",
        sa.Column("referral_outcome", sa.Text(), nullable=True),
    )
    op.create_table(
        "clinical_orders",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "clinic_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("clinics.id"),
            nullable=False,
        ),
        sa.Column(
            "patient_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("patients.id"),
            nullable=False,
        ),
        sa.Column(
            "appointment_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("appointments.id"),
            nullable=True,
        ),
        sa.Column("order_type", sa.String(16), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="ordered"),
        sa.Column("result_summary", sa.Text(), nullable=True),
        sa.Column(
            "patient_file_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("patient_files.id"),
            nullable=True,
        ),
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
        sa.CheckConstraint("order_type IN ('lab', 'imaging')", name="ck_clinical_orders_type"),
        sa.CheckConstraint(
            "status IN ('ordered', 'in_progress', 'resulted', 'cancelled')",
            name="ck_clinical_orders_status",
        ),
    )
    op.create_index("ix_clinical_orders_clinic_id", "clinical_orders", ["clinic_id"])
    op.create_index("ix_clinical_orders_patient_id", "clinical_orders", ["patient_id"])


def downgrade() -> None:
    op.drop_index("ix_clinical_orders_patient_id", table_name="clinical_orders")
    op.drop_index("ix_clinical_orders_clinic_id", table_name="clinical_orders")
    op.drop_table("clinical_orders")
    op.drop_column("documents_generated", "referral_outcome")
    op.drop_column("documents_generated", "referral_status")
    op.drop_column("documents_generated", "referral_recipient")

"""Prescriptions, line items, drug reference seed."""

import uuid
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "009_prescriptions"
down_revision: str | None = "008_soap_notes"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

DRUG_SEED = [
    {
        "id": str(uuid.uuid4()),
        "name": "Amoxicillin",
        "generic_name": "amoxicillin",
        "known_allergen_classes": ["penicillin"],
        "interaction_with": ["warfarin"],
    },
    {
        "id": str(uuid.uuid4()),
        "name": "Augmentin",
        "generic_name": "amoxicillin-clavulanate",
        "known_allergen_classes": ["penicillin"],
        "interaction_with": [],
    },
    {
        "id": str(uuid.uuid4()),
        "name": "Ibuprofen",
        "generic_name": "ibuprofen",
        "known_allergen_classes": ["nsaid"],
        "interaction_with": ["warfarin", "aspirin"],
    },
    {
        "id": str(uuid.uuid4()),
        "name": "Metformin",
        "generic_name": "metformin",
        "known_allergen_classes": [],
        "interaction_with": ["contrast dye"],
    },
    {
        "id": str(uuid.uuid4()),
        "name": "Warfarin",
        "generic_name": "warfarin",
        "known_allergen_classes": [],
        "interaction_with": ["ibuprofen", "aspirin", "amoxicillin"],
    },
    {
        "id": str(uuid.uuid4()),
        "name": "Aspirin",
        "generic_name": "aspirin",
        "known_allergen_classes": ["nsaid", "salicylate"],
        "interaction_with": ["warfarin", "ibuprofen"],
    },
    {
        "id": str(uuid.uuid4()),
        "name": "Paracetamol",
        "generic_name": "acetaminophen",
        "known_allergen_classes": [],
        "interaction_with": [],
    },
    {
        "id": str(uuid.uuid4()),
        "name": "Losartan",
        "generic_name": "losartan",
        "known_allergen_classes": [],
        "interaction_with": ["potassium supplements"],
    },
]


def upgrade() -> None:
    op.create_table(
        "drug_reference",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("generic_name", sa.String(length=128), nullable=False),
        sa.Column("known_allergen_classes", postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column("interaction_with", postgresql.ARRAY(sa.String()), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_drug_reference_name"),
    )

    op.create_table(
        "prescriptions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("patient_id", sa.UUID(), nullable=False),
        sa.Column("doctor_id", sa.UUID(), nullable=False),
        sa.Column("clinic_id", sa.UUID(), nullable=False),
        sa.Column("appointment_id", sa.UUID(), nullable=True),
        sa.Column("status", sa.String(length=16), server_default="draft", nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("pdf_object_key", sa.String(length=512), nullable=True),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("voided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("void_reason", sa.Text(), nullable=True),
        sa.Column("override_reason", sa.Text(), nullable=True),
        sa.Column("conflict_flags", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
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
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"]),
        sa.ForeignKeyConstraint(["doctor_id"], ["doctor_profiles.id"]),
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"]),
        sa.ForeignKeyConstraint(["appointment_id"], ["appointments.id"]),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_prescriptions_patient_id", "prescriptions", ["patient_id"])
    op.create_index("ix_prescriptions_clinic_id", "prescriptions", ["clinic_id"])

    op.create_table(
        "prescription_items",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("prescription_id", sa.UUID(), nullable=False),
        sa.Column("drug_name", sa.String(length=256), nullable=False),
        sa.Column("generic_name", sa.String(length=256), nullable=True),
        sa.Column("dosage", sa.String(length=128), nullable=True),
        sa.Column("form", sa.String(length=64), nullable=True),
        sa.Column("frequency", sa.String(length=128), nullable=True),
        sa.Column("duration", sa.String(length=128), nullable=True),
        sa.Column("quantity", sa.String(length=64), nullable=True),
        sa.Column("special_instructions", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.ForeignKeyConstraint(["prescription_id"], ["prescriptions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_prescription_items_prescription_id", "prescription_items", ["prescription_id"]
    )

    drug_table = sa.table(
        "drug_reference",
        sa.column("id", sa.UUID()),
        sa.column("name", sa.String()),
        sa.column("generic_name", sa.String()),
        sa.column("known_allergen_classes", postgresql.ARRAY(sa.String())),
        sa.column("interaction_with", postgresql.ARRAY(sa.String())),
    )
    op.bulk_insert(
        drug_table,
        [
            {
                "id": row["id"],
                "name": row["name"],
                "generic_name": row["generic_name"],
                "known_allergen_classes": row["known_allergen_classes"],
                "interaction_with": row["interaction_with"],
            }
            for row in DRUG_SEED
        ],
    )


def downgrade() -> None:
    op.drop_index("ix_prescription_items_prescription_id", table_name="prescription_items")
    op.drop_table("prescription_items")
    op.drop_index("ix_prescriptions_clinic_id", table_name="prescriptions")
    op.drop_index("ix_prescriptions_patient_id", table_name="prescriptions")
    op.drop_table("prescriptions")
    op.drop_table("drug_reference")

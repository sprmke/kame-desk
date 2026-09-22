"""Doctor specialty keys, optional user phone."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "041_doctor_specialty_key"
down_revision: str | None = "040_tooth_chart_fk_ondelete"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_LEGACY = {
    "dentist": "dentist",
    "dental": "dentist",
    "dentistry": "dentist",
    "ob-gyn": "obgyn",
    "obgyn": "obgyn",
    "ob/gyn": "obgyn",
    "obstetrics": "obgyn",
    "pediatrician": "pediatrician",
    "pediatrics": "pediatrician",
    "pedia": "pediatrician",
    "general practitioner": "general_practitioner",
    "general practice": "general_practitioner",
    "family medicine": "general_practitioner",
    "gp": "general_practitioner",
    "dermatologist": "dermatologist",
    "dermatology": "dermatologist",
    "cardiologist": "cardiologist",
    "cardiology": "cardiologist",
    "ophthalmologist": "ophthalmologist",
    "ophthalmology": "ophthalmologist",
    "orthopedic": "orthopedic",
    "orthopaedics": "orthopedic",
    "ent": "ent",
    "otolaryngology": "ent",
}


def upgrade() -> None:
    op.add_column("users", sa.Column("phone", sa.String(length=50), nullable=True))
    op.add_column(
        "doctor_profiles",
        sa.Column("specialty_key", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "doctor_profiles",
        sa.Column("specialty_other", sa.String(length=128), nullable=True),
    )

    bind = op.get_bind()
    rows = bind.execute(sa.text("SELECT id, specialty FROM doctor_profiles")).mappings()
    for row in rows:
        raw = (row["specialty"] or "").strip()
        mapped = _LEGACY.get(raw.lower())
        if mapped:
            bind.execute(
                sa.text(
                    "UPDATE doctor_profiles SET specialty_key = :key, specialty_other = NULL "
                    "WHERE id = :id"
                ),
                {"key": mapped, "id": row["id"]},
            )
        elif raw:
            bind.execute(
                sa.text(
                    "UPDATE doctor_profiles SET specialty_key = 'other', specialty_other = :other "
                    "WHERE id = :id"
                ),
                {"other": raw[:128], "id": row["id"]},
            )


def downgrade() -> None:
    op.drop_column("doctor_profiles", "specialty_other")
    op.drop_column("doctor_profiles", "specialty_key")
    op.drop_column("users", "phone")

"""Public booking slug, booking_source on appointments."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "004_public_booking_calendar"
down_revision: str | None = "003_patients_appointments"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("clinics", sa.Column("slug", sa.String(length=64), nullable=True))
    op.add_column(
        "clinics",
        sa.Column(
            "public_booking_auto_confirm",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
    )

    conn = op.get_bind()
    rows = conn.execute(sa.text("SELECT id, name FROM clinics")).fetchall()
    used: set[str] = set()
    for row in rows:
        base = _slugify(row.name)
        slug = base
        n = 2
        while slug in used:
            slug = f"{base}-{n}"
            n += 1
        used.add(slug)
        conn.execute(
            sa.text("UPDATE clinics SET slug = :slug WHERE id = :id"),
            {"slug": slug, "id": row.id},
        )

    op.alter_column("clinics", "slug", nullable=False)
    op.create_unique_constraint("uq_clinics_slug", "clinics", ["slug"])

    op.add_column(
        "appointments",
        sa.Column(
            "booking_source",
            sa.String(length=32),
            server_default="staff",
            nullable=False,
        ),
    )
    op.create_check_constraint(
        "ck_appointments_booking_source",
        "appointments",
        "booking_source IN ('staff', 'public_link', 'ai_assistant')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_appointments_booking_source", "appointments", type_="check")
    op.drop_column("appointments", "booking_source")
    op.drop_constraint("uq_clinics_slug", "clinics", type_="unique")
    op.drop_column("clinics", "public_booking_auto_confirm")
    op.drop_column("clinics", "slug")


def _slugify(name: str) -> str:
    import re

    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return (slug[:56] or "clinic")[:56]

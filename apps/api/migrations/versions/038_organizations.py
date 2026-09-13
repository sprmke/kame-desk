"""Organizations envelope above clinics (Phase 41)."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "038_organizations"
down_revision: str | None = "037_growth_retention"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "organizations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="trial", nullable=False),
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
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index("ix_organizations_owner_id", "organizations", ["owner_id"])
    op.create_index("ix_organizations_slug", "organizations", ["slug"])

    op.create_table(
        "organization_subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("plan_key", sa.String(length=32), server_default="starter", nullable=False),
        sa.Column("status", sa.String(length=20), server_default="trial", nullable=False),
        sa.Column("trial_ends_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id"),
    )

    op.create_table(
        "organization_enrolled_clinics",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("clinic_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "status",
            sa.String(length=32),
            server_default="pending_enrollment",
            nullable=False,
        ),
        sa.Column("enrolled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("clinic_id"),
        sa.UniqueConstraint("organization_id", "clinic_id", name="uq_org_enrolled_org_clinic"),
    )
    op.create_index(
        "ix_organization_enrolled_clinics_organization_id",
        "organization_enrolled_clinics",
        ["organization_id"],
    )
    op.create_index(
        "ix_organization_enrolled_clinics_clinic_id",
        "organization_enrolled_clinics",
        ["clinic_id"],
    )

    op.add_column(
        "clinics",
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index("ix_clinics_organization_id", "clinics", ["organization_id"])
    op.create_foreign_key(
        "fk_clinics_organization_id",
        "clinics",
        "organizations",
        ["organization_id"],
        ["id"],
    )

    # Backfill: one org per existing clinic
    op.execute(
        sa.text(
            """
            DO $$
            DECLARE
                r RECORD;
                org_id UUID;
                org_slug TEXT;
                n INT;
            BEGIN
                FOR r IN
                    SELECT DISTINCT ON (c.id)
                        c.id AS clinic_id,
                        c.name AS clinic_name,
                        c.slug AS clinic_slug,
                        COALESCE(c.plan_key, 'starter') AS plan_key,
                        COALESCE(c.status, 'trial') AS clinic_status,
                        cm.user_id AS owner_id
                    FROM clinics c
                    LEFT JOIN clinic_memberships cm ON cm.clinic_id = c.id
                        AND cm.role = 'owner' AND cm.is_active = true
                    ORDER BY c.id, cm.created_at ASC NULLS LAST
                LOOP
                    IF r.owner_id IS NULL THEN
                        SELECT user_id INTO r.owner_id
                        FROM clinic_memberships
                        WHERE clinic_id = r.clinic_id AND is_active = true
                        ORDER BY created_at ASC
                        LIMIT 1;
                    END IF;
                    IF r.owner_id IS NULL THEN
                        CONTINUE;
                    END IF;

                    org_slug := r.clinic_slug || '-org';
                    n := 2;
                    WHILE EXISTS (SELECT 1 FROM organizations WHERE slug = org_slug) LOOP
                        org_slug := r.clinic_slug || '-org-' || n;
                        n := n + 1;
                    END LOOP;

                    org_id := gen_random_uuid();
                    INSERT INTO organizations (id, owner_id, name, slug, status, created_at, updated_at)
                    VALUES (org_id, r.owner_id, r.clinic_name, org_slug, r.clinic_status, NOW(), NOW());

                    INSERT INTO organization_subscriptions (
                        id, organization_id, plan_key, status, created_at, updated_at
                    ) VALUES (
                        gen_random_uuid(), org_id, r.plan_key, r.clinic_status, NOW(), NOW()
                    );

                    INSERT INTO organization_enrolled_clinics (
                        id, organization_id, clinic_id, status, enrolled_at, created_at
                    ) VALUES (
                        gen_random_uuid(), org_id, r.clinic_id, 'active', NOW(), NOW()
                    );

                    UPDATE clinics SET organization_id = org_id WHERE id = r.clinic_id;
                END LOOP;
            END $$;
            """
        )
    )

    op.alter_column("clinics", "organization_id", nullable=False)
    op.alter_column("clinics", "plan_key", nullable=True)


def downgrade() -> None:
    op.alter_column("clinics", "plan_key", nullable=False, server_default="starter")
    op.drop_constraint("fk_clinics_organization_id", "clinics", type_="foreignkey")
    op.drop_index("ix_clinics_organization_id", table_name="clinics")
    op.drop_column("clinics", "organization_id")
    op.drop_table("organization_enrolled_clinics")
    op.drop_table("organization_subscriptions")
    op.drop_table("organizations")

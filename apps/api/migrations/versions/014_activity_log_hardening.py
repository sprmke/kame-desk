"""Activity log indexes and append-only trigger."""

from collections.abc import Sequence

from alembic import op

revision: str = "014_activity_log_hardening"
down_revision: str | None = "013_reporting_indexes"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "ix_activity_log_clinic_created_at",
        "activity_log",
        ["clinic_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_activity_log_target",
        "activity_log",
        ["target_type", "target_id"],
        unique=False,
    )
    op.execute(
        """
        CREATE OR REPLACE FUNCTION activity_log_deny_mutations()
        RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'activity_log is append-only';
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER activity_log_no_update
        BEFORE UPDATE OR DELETE ON activity_log
        FOR EACH ROW EXECUTE FUNCTION activity_log_deny_mutations();
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS activity_log_no_update ON activity_log")
    op.execute("DROP FUNCTION IF EXISTS activity_log_deny_mutations()")
    op.drop_index("ix_activity_log_target", table_name="activity_log")
    op.drop_index("ix_activity_log_clinic_created_at", table_name="activity_log")

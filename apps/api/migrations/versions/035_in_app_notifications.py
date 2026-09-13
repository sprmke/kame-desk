"""In-app staff notifications, read state, push subscriptions."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "035_in_app_notifications"
down_revision: str | None = "034_soap_client_draft_token"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

NOTIFICATION_TYPES = (
    "appointment.public_booked",
    "appointment.needs_confirm",
    "appointment.patient_reschedule_requested",
    "appointment.cancelled",
    "appointment.no_show",
    "appointment.rescheduled",
    "visit.arrived",
    "visit.completed",
    "waitlist.created",
    "waitlist.slot_offered",
    "prescription.issued",
    "document.issued",
    "transcription.ready",
    "visit_summary.failed",
    "clinical_order.updated",
    "invoice.payment_recorded",
    "invoice.voided",
    "invoice.credit_issued",
    "insurance_claim.denied",
    "loa_request.status_changed",
    "eligibility_check.updated",
    "reminder.send_failed",
    "messaging.inbound",
    "staff.joined",
    "membership.role_changed",
    "auth.refresh_reuse",
    "clinic.deletion_requested",
)

TYPE_CHECK = ", ".join(f"'{t}'" for t in NOTIFICATION_TYPES)


def upgrade() -> None:
    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "clinic_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("clinics.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("type", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("entity_type", sa.String(length=64), nullable=True),
        sa.Column("entity_id", sa.String(length=64), nullable=True),
        sa.Column("href", sa.String(length=512), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("dedupe_key", sa.String(length=255), nullable=True),
        sa.Column(
            "actor_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("audience_roles", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column(
            "target_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "target_doctor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("doctor_profiles.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(f"type IN ({TYPE_CHECK})", name="notifications_type_check"),
    )
    op.create_index("ix_notifications_clinic_created", "notifications", ["clinic_id", "created_at"])
    op.create_index(
        "notifications_clinic_type_dedupe_key_unique",
        "notifications",
        ["clinic_id", "type", "dedupe_key"],
        unique=True,
        postgresql_where=sa.text("dedupe_key IS NOT NULL"),
    )

    op.create_table(
        "notification_reads",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "notification_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("notifications.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "read_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "notification_id", "user_id", name="uq_notification_reads_notification_user"
        ),
    )
    op.create_index("ix_notification_reads_user_id", "notification_reads", ["user_id"])

    op.add_column(
        "clinic_memberships",
        sa.Column(
            "in_app_notification_prefs",
            postgresql.JSONB(),
            nullable=True,
        ),
    )

    op.create_table(
        "push_subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "clinic_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("clinics.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("endpoint", sa.Text(), nullable=False),
        sa.Column("p256dh", sa.String(length=255), nullable=False),
        sa.Column("auth", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("endpoint", name="uq_push_subscriptions_endpoint"),
    )
    op.create_index(
        "ix_push_subscriptions_user_clinic", "push_subscriptions", ["user_id", "clinic_id"]
    )


def downgrade() -> None:
    op.drop_table("push_subscriptions")
    op.drop_column("clinic_memberships", "in_app_notification_prefs")
    op.drop_table("notification_reads")
    op.drop_table("notifications")

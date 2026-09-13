"""AI Clinic Assistant tables and clinic toggle."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "017_ai_assistant"
down_revision: str | None = "016_transcription_embeddings"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "clinics",
        sa.Column(
            "ai_assistant_enabled",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
    )

    op.create_table(
        "ai_assistant_conversations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "clinic_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("clinics.id"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
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
    )
    op.create_index(
        "ix_ai_assistant_conversations_clinic_user",
        "ai_assistant_conversations",
        ["clinic_id", "user_id"],
    )

    op.create_table(
        "ai_assistant_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "conversation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("ai_assistant_conversations.id"),
            nullable=False,
        ),
        sa.Column("role", sa.String(16), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_ai_assistant_messages_conversation_id",
        "ai_assistant_messages",
        ["conversation_id"],
    )

    op.create_table(
        "ai_assistant_actions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "conversation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("ai_assistant_conversations.id"),
            nullable=False,
        ),
        sa.Column(
            "message_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("ai_assistant_messages.id"),
            nullable=True,
        ),
        sa.Column("tool_name", sa.String(64), nullable=False),
        sa.Column("tier", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(32), server_default="pending", nullable=False),
        sa.Column("proposal", postgresql.JSONB(), nullable=False),
        sa.Column("result", postgresql.JSONB(), nullable=True),
        sa.Column("external_send", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_ai_assistant_actions_conversation_id", "ai_assistant_actions", ["conversation_id"]
    )
    op.create_index("ix_ai_assistant_actions_status", "ai_assistant_actions", ["status"])


def downgrade() -> None:
    op.drop_index("ix_ai_assistant_actions_status", table_name="ai_assistant_actions")
    op.drop_index("ix_ai_assistant_actions_conversation_id", table_name="ai_assistant_actions")
    op.drop_table("ai_assistant_actions")
    op.drop_index("ix_ai_assistant_messages_conversation_id", table_name="ai_assistant_messages")
    op.drop_table("ai_assistant_messages")
    op.drop_index(
        "ix_ai_assistant_conversations_clinic_user", table_name="ai_assistant_conversations"
    )
    op.drop_table("ai_assistant_conversations")
    op.drop_column("clinics", "ai_assistant_enabled")

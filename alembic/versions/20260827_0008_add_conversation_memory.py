"""add conversation memory

Revision ID: 20260827_0008
Revises: 20260826_0007
Create Date: 2026-08-27
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import (
    postgresql,
)


revision: str = "20260827_0008"
down_revision: str | None = (
    "20260826_0007"
)
branch_labels: (
    str | Sequence[str] | None
) = None
depends_on: (
    str | Sequence[str] | None
) = None


def upgrade() -> None:
    op.create_table(
        "conversations",
        sa.Column(
            "id",
            sa.Integer(),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column(
            "conversation_id",
            sa.String(length=36),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.String(),
            nullable=False,
        ),
        sa.Column(
            "title",
            sa.String(length=160),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.user_id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "id",
        ),
        sa.UniqueConstraint(
            "conversation_id",
        ),
        sa.UniqueConstraint(
            "conversation_id",
            "user_id",
            name=(
                "uq_conversations_"
                "conversation_id_user_id"
            ),
        ),
    )

    op.create_index(
        op.f(
            "ix_conversations_"
            "conversation_id"
        ),
        "conversations",
        ["conversation_id"],
        unique=True,
    )

    op.create_index(
        op.f(
            "ix_conversations_user_id"
        ),
        "conversations",
        ["user_id"],
        unique=False,
    )

    op.create_table(
        "conversation_messages",
        sa.Column(
            "id",
            sa.Integer(),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column(
            "message_id",
            sa.String(length=36),
            nullable=False,
        ),
        sa.Column(
            "conversation_id",
            sa.String(length=36),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.String(),
            nullable=False,
        ),
        sa.Column(
            "role",
            sa.String(length=16),
            nullable=False,
        ),
        sa.Column(
            "content",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "route",
            sa.String(length=32),
            nullable=True,
        ),
        sa.Column(
            "document_ids",
            postgresql.JSONB(
                astext_type=sa.Text(),
            ),
            nullable=False,
        ),
        sa.Column(
            "sources",
            postgresql.JSONB(
                astext_type=sa.Text(),
            ),
            nullable=False,
        ),
        sa.Column(
            "safety_category",
            sa.String(length=64),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "role IN ('user', 'assistant')",
            name=(
                "ck_conversation_messages_role"
            ),
        ),
        sa.ForeignKeyConstraint(
            [
                "conversation_id",
                "user_id",
            ],
            [
                "conversations."
                "conversation_id",
                "conversations.user_id",
            ],
            name=(
                "fk_conversation_messages_"
                "conversation_owner"
            ),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "id",
        ),
        sa.UniqueConstraint(
            "message_id",
        ),
    )

    op.create_index(
        op.f(
            "ix_conversation_messages_"
            "message_id"
        ),
        "conversation_messages",
        ["message_id"],
        unique=True,
    )

    op.create_index(
        op.f(
            "ix_conversation_messages_"
            "conversation_id"
        ),
        "conversation_messages",
        ["conversation_id"],
        unique=False,
    )

    op.create_index(
        op.f(
            "ix_conversation_messages_"
            "user_id"
        ),
        "conversation_messages",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f(
            "ix_conversation_messages_"
            "user_id"
        ),
        table_name=(
            "conversation_messages"
        ),
    )

    op.drop_index(
        op.f(
            "ix_conversation_messages_"
            "conversation_id"
        ),
        table_name=(
            "conversation_messages"
        ),
    )

    op.drop_index(
        op.f(
            "ix_conversation_messages_"
            "message_id"
        ),
        table_name=(
            "conversation_messages"
        ),
    )

    op.drop_table(
        "conversation_messages"
    )

    op.drop_index(
        op.f(
            "ix_conversations_user_id"
        ),
        table_name="conversations",
    )

    op.drop_index(
        op.f(
            "ix_conversations_"
            "conversation_id"
        ),
        table_name="conversations",
    )

    op.drop_table(
        "conversations"
    )
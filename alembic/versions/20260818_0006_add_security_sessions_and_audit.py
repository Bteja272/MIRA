"""Add refresh sessions and audit events.

Revision ID: 20260818_0006
Revises: 20260723_0005
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import (
    postgresql,
)


revision = "20260818_0006"
down_revision = "20260723_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "refresh_sessions",
        sa.Column(
            "id",
            sa.BigInteger(),
            primary_key=True,
            autoincrement=True,
        ),
        sa.Column(
            "session_id",
            sa.String(
                length=36
            ),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.String(
                length=100
            ),
            nullable=False,
        ),
        sa.Column(
            "token_hash",
            sa.String(
                length=64
            ),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=False,
        ),
        sa.Column(
            "expires_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=False,
        ),
        sa.Column(
            "last_used_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=True,
        ),
        sa.Column(
            "revoked_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=True,
        ),
        sa.Column(
            "replaced_by_session_id",
            sa.String(
                length=36
            ),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.user_id"],
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "session_id",
            name=(
                "uq_refresh_sessions_"
                "session_id"
            ),
        ),
    )

    op.create_index(
        "ix_refresh_sessions_user_id",
        "refresh_sessions",
        ["user_id"],
    )

    op.create_index(
        "ix_refresh_sessions_expires_at",
        "refresh_sessions",
        ["expires_at"],
    )

    op.create_table(
        "audit_events",
        sa.Column(
            "id",
            sa.BigInteger(),
            primary_key=True,
            autoincrement=True,
        ),
        sa.Column(
            "event_id",
            sa.String(
                length=36
            ),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.String(
                length=100
            ),
            nullable=True,
        ),
        sa.Column(
            "event_type",
            sa.String(
                length=64
            ),
            nullable=False,
        ),
        sa.Column(
            "outcome",
            sa.String(
                length=32
            ),
            nullable=False,
        ),
        sa.Column(
            "resource_type",
            sa.String(
                length=64
            ),
            nullable=True,
        ),
        sa.Column(
            "resource_id",
            sa.String(
                length=128
            ),
            nullable=True,
        ),
        sa.Column(
            "details",
            postgresql.JSONB(
                astext_type=sa.Text()
            ),
            nullable=False,
            server_default=(
                sa.text(
                    "'{}'::jsonb"
                )
            ),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.user_id"],
            ondelete="SET NULL",
        ),
        sa.UniqueConstraint(
            "event_id",
            name=(
                "uq_audit_events_event_id"
            ),
        ),
    )

    op.create_index(
        "ix_audit_events_user_id",
        "audit_events",
        ["user_id"],
    )

    op.create_index(
        "ix_audit_events_event_type",
        "audit_events",
        ["event_type"],
    )

    op.create_index(
        "ix_audit_events_created_at",
        "audit_events",
        ["created_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_audit_events_created_at",
        table_name="audit_events",
    )

    op.drop_index(
        "ix_audit_events_event_type",
        table_name="audit_events",
    )

    op.drop_index(
        "ix_audit_events_user_id",
        table_name="audit_events",
    )

    op.drop_table(
        "audit_events"
    )

    op.drop_index(
        "ix_refresh_sessions_expires_at",
        table_name="refresh_sessions",
    )

    op.drop_index(
        "ix_refresh_sessions_user_id",
        table_name="refresh_sessions",
    )

    op.drop_table(
        "refresh_sessions"
    )
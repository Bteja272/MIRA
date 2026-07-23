"""Require every document to have an owner.

Revision ID: 20260722_0004
Revises: 20260722_0003
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260722_0004"
down_revision: str | None = "20260722_0003"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    connection = op.get_bind()

    ownerless_document_count = connection.execute(
        sa.text(
            """
            SELECT COUNT(*)
            FROM documents
            WHERE user_id IS NULL
            """
        )
    ).scalar_one()

    if ownerless_document_count:
        raise RuntimeError(
            "Cannot make documents.user_id non-nullable: "
            f"{ownerless_document_count} ownerless "
            "document(s) still exist. Delete or migrate "
            "those records before applying this migration."
        )

    op.alter_column(
        "documents",
        "user_id",
        existing_type=sa.String(),
        existing_nullable=True,
        nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "documents",
        "user_id",
        existing_type=sa.String(),
        existing_nullable=False,
        nullable=True,
    )
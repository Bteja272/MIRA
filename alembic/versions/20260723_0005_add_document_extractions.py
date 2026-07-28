"""Add persisted structured medical extractions.

Revision ID: 20260723_0005
Revises: 20260722_0004
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import (
    postgresql,
)


revision: str = "20260723_0005"
down_revision: str | None = (
    "20260722_0004"
)
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_documents_document_id_user_id",
        "documents",
        [
            "document_id",
            "user_id",
        ],
    )

    op.create_table(
        "document_extractions",
        sa.Column(
            "id",
            sa.Integer(),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column(
            "extraction_id",
            sa.String(length=36),
            nullable=False,
        ),
        sa.Column(
            "document_id",
            sa.String(),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.String(),
            nullable=False,
        ),
        sa.Column(
            "schema_version",
            sa.String(length=20),
            nullable=False,
            server_default="1.0",
        ),
        sa.Column(
            "status",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "extraction_method",
            sa.String(length=50),
            nullable=False,
            server_default="hybrid",
        ),
        sa.Column(
            "model_name",
            sa.String(length=200),
            nullable=False,
        ),
        sa.Column(
            "extraction_data",
            postgresql.JSONB(
                astext_type=sa.Text()
            ),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=(
                sa.text(
                    "CURRENT_TIMESTAMP"
                )
            ),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=(
                sa.text(
                    "CURRENT_TIMESTAMP"
                )
            ),
        ),
        sa.ForeignKeyConstraint(
            [
                "document_id",
                "user_id",
            ],
            [
                "documents.document_id",
                "documents.user_id",
            ],
            name=(
                "fk_document_extractions_"
                "document_owner"
            ),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "id",
            name=(
                "pk_document_extractions"
            ),
        ),
        sa.UniqueConstraint(
            "extraction_id",
            name=(
                "uq_document_extractions_"
                "extraction_id"
            ),
        ),
        sa.UniqueConstraint(
            "document_id",
            name=(
                "uq_document_extractions_"
                "document_id"
            ),
        ),
    )

    op.create_index(
        "ix_document_extractions_"
        "user_id_updated_at",
        "document_extractions",
        [
            "user_id",
            "updated_at",
        ],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_document_extractions_"
        "user_id_updated_at",
        table_name=(
            "document_extractions"
        ),
    )

    op.drop_table(
        "document_extractions"
    )

    op.drop_constraint(
        "uq_documents_document_id_user_id",
        "documents",
        type_="unique",
    )
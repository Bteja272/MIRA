"""Add persisted medical intelligence.

Revision ID: 20260826_0007
Revises: 20260818_0006
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import (
    postgresql,
)


revision = "20260826_0007"
down_revision = "20260818_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "document_intelligence",
        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True,
            autoincrement=True,
        ),
        sa.Column(
            "intelligence_id",
            sa.String(
                length=36
            ),
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
            "source_extraction_id",
            sa.String(
                length=36
            ),
            nullable=False,
        ),
        sa.Column(
            "source_extraction_updated_at",
            sa.DateTime(),
            nullable=False,
        ),
        sa.Column(
            "schema_version",
            sa.String(
                length=20
            ),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(
                length=50
            ),
            nullable=False,
        ),
        sa.Column(
            "intelligence_data",
            postgresql.JSONB(
                astext_type=sa.Text()
            ),
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
            [
                "document_id",
                "user_id",
            ],
            [
                "documents.document_id",
                "documents.user_id",
            ],
            name=(
                "fk_document_intelligence_"
                "document_owner"
            ),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            [
                "source_extraction_id",
            ],
            [
                (
                    "document_extractions."
                    "extraction_id"
                ),
            ],
            name=(
                "fk_document_intelligence_"
                "source_extraction"
            ),
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "intelligence_id",
            name=(
                "uq_document_intelligence_"
                "intelligence_id"
            ),
        ),
        sa.UniqueConstraint(
            "document_id",
            name=(
                "uq_document_intelligence_"
                "document_id"
            ),
        ),
    )

    op.create_index(
        (
            "ix_document_intelligence_"
            "user_id_updated_at"
        ),
        "document_intelligence",
        [
            "user_id",
            "updated_at",
        ],
    )


def downgrade() -> None:
    op.drop_index(
        (
            "ix_document_intelligence_"
            "user_id_updated_at"
        ),
        table_name=(
            "document_intelligence"
        ),
    )

    op.drop_table(
        "document_intelligence"
    )
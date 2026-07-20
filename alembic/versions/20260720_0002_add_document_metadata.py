"""Add document metadata and future ownership fields.

Revision ID: 20260720_0002
Revises: 20260720_0001
"""

from alembic import op
import sqlalchemy as sa


revision = "20260720_0002"
down_revision = "20260720_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "documents",
        sa.Column(
            "user_id",
            sa.String(),
            nullable=True,
        ),
    )

    op.add_column(
        "documents",
        sa.Column(
            "original_filename",
            sa.String(),
            nullable=True,
        ),
    )

    op.add_column(
        "documents",
        sa.Column(
            "stored_filename",
            sa.String(),
            nullable=True,
        ),
    )

    op.add_column(
        "documents",
        sa.Column(
            "document_type",
            sa.String(),
            nullable=True,
            server_default="unknown",
        ),
    )

    op.add_column(
        "documents",
        sa.Column(
            "file_hash",
            sa.String(length=64),
            nullable=True,
        ),
    )

    op.add_column(
        "documents",
        sa.Column(
            "file_size_bytes",
            sa.BigInteger(),
            nullable=True,
        ),
    )

    # Preserve existing rows created before metadata support.
    op.execute(
        """
        UPDATE documents
        SET
            original_filename =
                COALESCE(NULLIF(source, ''), document_id),
            stored_filename =
                COALESCE(NULLIF(source, ''), document_id),
            document_type =
                COALESCE(document_type, 'unknown')
        """
    )

    op.alter_column(
        "documents",
        "original_filename",
        existing_type=sa.String(),
        nullable=False,
    )

    op.alter_column(
        "documents",
        "stored_filename",
        existing_type=sa.String(),
        nullable=False,
    )

    op.alter_column(
        "documents",
        "document_type",
        existing_type=sa.String(),
        nullable=False,
        server_default="unknown",
    )

    op.create_index(
        "ix_documents_user_id",
        "documents",
        ["user_id"],
        unique=False,
    )

    op.create_index(
        "ix_documents_document_type",
        "documents",
        ["document_type"],
        unique=False,
    )

    op.create_index(
        "ix_documents_file_hash",
        "documents",
        ["file_hash"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_documents_file_hash",
        table_name="documents",
    )

    op.drop_index(
        "ix_documents_document_type",
        table_name="documents",
    )

    op.drop_index(
        "ix_documents_user_id",
        table_name="documents",
    )

    op.drop_column(
        "documents",
        "file_size_bytes",
    )

    op.drop_column(
        "documents",
        "file_hash",
    )

    op.drop_column(
        "documents",
        "document_type",
    )

    op.drop_column(
        "documents",
        "stored_filename",
    )

    op.drop_column(
        "documents",
        "original_filename",
    )

    op.drop_column(
        "documents",
        "user_id",
    )
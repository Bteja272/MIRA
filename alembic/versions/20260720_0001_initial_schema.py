"""Create the original MIRA document schema.

Revision ID: 20260720_0001
Revises:
"""

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


revision = "20260720_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "CREATE EXTENSION IF NOT EXISTS vector"
    )

    op.create_table(
        "documents",
        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True,
            autoincrement=True,
        ),
        sa.Column(
            "document_id",
            sa.String(),
            nullable=False,
        ),
        sa.Column(
            "source",
            sa.String(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )

    op.create_index(
        "ix_documents_document_id",
        "documents",
        ["document_id"],
        unique=True,
    )

    op.create_table(
        "document_chunks",
        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True,
            autoincrement=True,
        ),
        sa.Column(
            "chunk_id",
            sa.String(),
            nullable=False,
        ),
        sa.Column(
            "document_id",
            sa.String(),
            nullable=False,
        ),
        sa.Column(
            "page_number",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "chunk_index",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "text",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "embedding",
            Vector(384),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["documents.document_id"],
            ondelete="CASCADE",
        ),
    )

    op.create_index(
        "ix_document_chunks_chunk_id",
        "document_chunks",
        ["chunk_id"],
        unique=True,
    )

    op.create_index(
        "ix_document_chunks_document_id",
        "document_chunks",
        ["document_id"],
        unique=False,
    )

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS
        ix_document_chunks_embedding_hnsw
        ON document_chunks
        USING hnsw (embedding vector_cosine_ops)
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP INDEX IF EXISTS
        ix_document_chunks_embedding_hnsw
        """
    )

    op.drop_index(
        "ix_document_chunks_document_id",
        table_name="document_chunks",
    )

    op.drop_index(
        "ix_document_chunks_chunk_id",
        table_name="document_chunks",
    )

    op.drop_table("document_chunks")

    op.drop_index(
        "ix_documents_document_id",
        table_name="documents",
    )

    op.drop_table("documents")
from datetime import datetime
from typing import Any

from sqlalchemy import (
    DateTime,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from app.db.base import Base


class DocumentExtraction(Base):
    """
    Persisted structured medical extraction.

    The composite foreign key guarantees that user_id matches
    the owner of the referenced document.
    """

    __tablename__ = "document_extractions"

    __table_args__ = (
        ForeignKeyConstraint(
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
        UniqueConstraint(
            "extraction_id",
            name=(
                "uq_document_extractions_"
                "extraction_id"
            ),
        ),
        UniqueConstraint(
            "document_id",
            name=(
                "uq_document_extractions_"
                "document_id"
            ),
        ),
        Index(
            "ix_document_extractions_"
            "user_id_updated_at",
            "user_id",
            "updated_at",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    extraction_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
    )

    document_id: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    user_id: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    schema_version: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="1.0",
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    extraction_method: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="hybrid",
    )

    model_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    extraction_data: Mapped[
        dict[str, Any]
    ] = mapped_column(
        JSONB,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
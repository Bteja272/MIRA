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
from sqlalchemy.dialects.postgresql import (
    JSONB,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from app.db.base import Base


class DocumentIntelligence(Base):
    """
    Persisted medical intelligence generated from a
    structured extraction.

    Ownership is enforced using the same composite
    document_id + user_id relationship used by
    structured extraction.

    source_extraction_id also references the source
    extraction. Deleting that extraction therefore
    removes the derived intelligence automatically.
    """

    __tablename__ = (
        "document_intelligence"
    )

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
                "fk_document_intelligence_"
                "document_owner"
            ),
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
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
        UniqueConstraint(
            "intelligence_id",
            name=(
                "uq_document_intelligence_"
                "intelligence_id"
            ),
        ),
        UniqueConstraint(
            "document_id",
            name=(
                "uq_document_intelligence_"
                "document_id"
            ),
        ),
        Index(
            (
                "ix_document_intelligence_"
                "user_id_updated_at"
            ),
            "user_id",
            "updated_at",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    intelligence_id: Mapped[str] = (
        mapped_column(
            String(36),
            nullable=False,
        )
    )

    document_id: Mapped[str] = (
        mapped_column(
            String,
            nullable=False,
        )
    )

    user_id: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    source_extraction_id: Mapped[str] = (
        mapped_column(
            String(36),
            nullable=False,
        )
    )

    source_extraction_updated_at: (
        Mapped[datetime]
    ) = mapped_column(
        DateTime,
        nullable=False,
    )

    schema_version: Mapped[str] = (
        mapped_column(
            String(20),
            nullable=False,
            default="1.0",
        )
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    intelligence_data: Mapped[
        dict[str, Any]
    ] = mapped_column(
        JSONB,
        nullable=False,
    )

    created_at: Mapped[datetime] = (
        mapped_column(
            DateTime,
            nullable=False,
            default=datetime.utcnow,
        )
    )

    updated_at: Mapped[datetime] = (
        mapped_column(
            DateTime,
            nullable=False,
            default=datetime.utcnow,
            onupdate=datetime.utcnow,
        )
    )
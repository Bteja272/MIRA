from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import (
    JSONB,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.db.base import Base


class Conversation(Base):
    __tablename__ = "conversations"

    __table_args__ = (
        UniqueConstraint(
            "conversation_id",
            "user_id",
            name=(
                "uq_conversations_"
                "conversation_id_user_id"
            ),
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    conversation_id: Mapped[str] = (
        mapped_column(
            String(36),
            unique=True,
            index=True,
            nullable=False,
        )
    )

    user_id: Mapped[str] = mapped_column(
        String,
        ForeignKey(
            "users.user_id",
            ondelete="CASCADE",
        ),
        index=True,
        nullable=False,
    )

    title: Mapped[str] = mapped_column(
        String(160),
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

    messages: Mapped[
        list[ConversationMessage]
    ] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by=(
            "ConversationMessage.created_at"
        ),
    )


class ConversationMessage(Base):
    __tablename__ = (
        "conversation_messages"
    )

    __table_args__ = (
        ForeignKeyConstraint(
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
        CheckConstraint(
            "role IN ('user', 'assistant')",
            name=(
                "ck_conversation_messages_role"
            ),
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    message_id: Mapped[str] = (
        mapped_column(
            String(36),
            unique=True,
            index=True,
            nullable=False,
        )
    )

    conversation_id: Mapped[str] = (
        mapped_column(
            String(36),
            index=True,
            nullable=False,
        )
    )

    user_id: Mapped[str] = mapped_column(
        String,
        index=True,
        nullable=False,
    )

    role: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    route: Mapped[
        str | None
    ] = mapped_column(
        String(32),
        nullable=True,
    )

    document_ids: Mapped[list] = (
        mapped_column(
            JSONB,
            nullable=False,
            default=list,
        )
    )

    sources: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )

    safety_category: Mapped[
        str | None
    ] = mapped_column(
        String(64),
        nullable=True,
    )

    created_at: Mapped[datetime] = (
        mapped_column(
            DateTime,
            nullable=False,
            default=datetime.utcnow,
        )
    )

    conversation: Mapped[
        Conversation
    ] = relationship(
        back_populates="messages",
    )
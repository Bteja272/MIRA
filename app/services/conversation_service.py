from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    func,
    select,
)

from app.db.conversation_models import (
    Conversation,
    ConversationMessage,
)
from app.db.session import SessionLocal
from app.services.medical_prompt_service import (
    MedicalPromptService,
)


class ConversationNotFoundError(
    RuntimeError
):
    pass


class ConversationService:
    MAX_CONTEXT_MESSAGES = 6
    MAX_CONTEXT_CHARACTERS = 6000
    MAX_CONTEXT_MESSAGE_CHARACTERS = (
        2000
    )

    @staticmethod
    def _clean_title(
        query: str,
    ) -> str:
        cleaned = " ".join(
            query.strip().split()
        )

        if not cleaned:
            return "MIRA conversation"

        if len(cleaned) <= 100:
            return cleaned

        return (
            cleaned[:97].rstrip()
            + "..."
        )

    @staticmethod
    def _context_content(
        content: str,
        role: str,
    ) -> str:
        cleaned = (
            content or ""
        ).strip()

        if role == "assistant":
            disclaimer = (
                MedicalPromptService
                .DISCLAIMER
            )

            cleaned = cleaned.replace(
                f"\n\n{disclaimer}",
                "",
            )

            if cleaned == disclaimer:
                cleaned = ""

        if (
            len(cleaned)
            > ConversationService
            .MAX_CONTEXT_MESSAGE_CHARACTERS
        ):
            cleaned = (
                cleaned[
                    :ConversationService
                    .MAX_CONTEXT_MESSAGE_CHARACTERS
                ]
                .rstrip()
                + "..."
            )

        return cleaned

    @classmethod
    def exists_for_user(
        cls,
        *,
        conversation_id: str,
        user_id: str,
    ) -> bool:
        statement = select(
            Conversation.id
        ).where(
            Conversation.conversation_id
            == conversation_id,
            Conversation.user_id
            == user_id,
        )

        db = SessionLocal()

        try:
            return (
                db.scalar(statement)
                is not None
            )

        finally:
            db.close()

    @classmethod
    def require_owned(
        cls,
        *,
        conversation_id: str,
        user_id: str,
    ) -> None:
        if not cls.exists_for_user(
            conversation_id=(
                conversation_id
            ),
            user_id=user_id,
        ):
            raise (
                ConversationNotFoundError(
                    "Conversation not found."
                )
            )

    @classmethod
    def get_context(
        cls,
        *,
        conversation_id: str,
        user_id: str,
    ) -> list[dict[str, str]]:
        statement = (
            select(
                ConversationMessage
            )
            .where(
                ConversationMessage
                .conversation_id
                == conversation_id,
                ConversationMessage.user_id
                == user_id,
            )
            .order_by(
                ConversationMessage
                .created_at.desc(),
                ConversationMessage.id.desc(),
            )
            .limit(
                cls.MAX_CONTEXT_MESSAGES
            )
        )

        db = SessionLocal()

        try:
            messages = list(
                db.scalars(
                    statement
                ).all()
            )

        finally:
            db.close()

        messages.reverse()

        context: list[
            dict[str, str]
        ] = []

        remaining_characters = (
            cls.MAX_CONTEXT_CHARACTERS
        )

        for message in reversed(
            messages
        ):
            cleaned = cls._context_content(
                message.content,
                message.role,
            )

            if not cleaned:
                continue

            if remaining_characters <= 0:
                break

            if (
                len(cleaned)
                > remaining_characters
            ):
                cleaned = (
                    cleaned[
                        -remaining_characters:
                    ]
                )

            context.append(
                {
                    "role": message.role,
                    "content": cleaned,
                }
            )

            remaining_characters -= len(
                cleaned
            )

        context.reverse()

        return context

    @classmethod
    def persist_exchange(
        cls,
        *,
        conversation_id: (
            str | None
        ),
        user_id: str,
        query: str,
        result: dict,
    ) -> tuple[str, str]:
        resolved_conversation_id = (
            conversation_id
            or str(uuid4())
        )

        assistant_message_id = (
            str(uuid4())
        )

        user_message_id = str(
            uuid4()
        )

        db = SessionLocal()

        try:
            conversation = db.scalar(
                select(
                    Conversation
                ).where(
                    Conversation
                    .conversation_id
                    == resolved_conversation_id,
                    Conversation.user_id
                    == user_id,
                )
            )

            if conversation is None:
                if conversation_id:
                    raise (
                        ConversationNotFoundError(
                            "Conversation not found."
                        )
                    )

                conversation = (
                    Conversation(
                        conversation_id=(
                            resolved_conversation_id
                        ),
                        user_id=user_id,
                        title=(
                            cls._clean_title(
                                query
                            )
                        ),
                    )
                )

                db.add(
                    conversation
                )

            user_message = (
                ConversationMessage(
                    message_id=(
                        user_message_id
                    ),
                    conversation_id=(
                        resolved_conversation_id
                    ),
                    user_id=user_id,
                    role="user",
                    content=query,
                    route=None,
                    document_ids=list(
                        result.get(
                            "document_ids",
                            [],
                        )
                        or []
                    ),
                    sources=[],
                    safety_category=None,
                )
            )

            assistant_message = (
                ConversationMessage(
                    message_id=(
                        assistant_message_id
                    ),
                    conversation_id=(
                        resolved_conversation_id
                    ),
                    user_id=user_id,
                    role="assistant",
                    content=str(
                        result.get(
                            "answer",
                            "",
                        )
                        or ""
                    ),
                    route=str(
                        result.get(
                            "route",
                            "direct",
                        )
                    ),
                    document_ids=list(
                        result.get(
                            "document_ids",
                            [],
                        )
                        or []
                    ),
                    sources=list(
                        result.get(
                            "sources",
                            [],
                        )
                        or []
                    ),
                    safety_category=(
                        result.get(
                            "safety_category"
                        )
                    ),
                )
            )

            db.add(
                user_message
            )
            db.add(
                assistant_message
            )

            conversation.updated_at = (
                datetime.utcnow()
            )

            db.commit()

            return (
                resolved_conversation_id,
                assistant_message_id,
            )

        except Exception:
            db.rollback()
            raise

        finally:
            db.close()

    @classmethod
    def list_for_user(
        cls,
        *,
        user_id: str,
    ) -> list[dict]:
        message_count = (
            select(
                func.count(
                    ConversationMessage.id
                )
            )
            .where(
                ConversationMessage
                .conversation_id
                == Conversation
                .conversation_id,
                ConversationMessage.user_id
                == Conversation.user_id,
            )
            .correlate(
                Conversation
            )
            .scalar_subquery()
        )

        statement = (
            select(
                Conversation,
                message_count.label(
                    "message_count"
                ),
            )
            .where(
                Conversation.user_id
                == user_id
            )
            .order_by(
                Conversation
                .updated_at.desc(),
                Conversation.id.desc(),
            )
        )

        db = SessionLocal()

        try:
            rows = db.execute(
                statement
            ).all()

            return [
                {
                    "conversation_id": (
                        conversation
                        .conversation_id
                    ),
                    "title": (
                        conversation.title
                    ),
                    "message_count": int(
                        count or 0
                    ),
                    "created_at": (
                        conversation
                        .created_at
                    ),
                    "updated_at": (
                        conversation
                        .updated_at
                    ),
                }
                for (
                    conversation,
                    count,
                ) in rows
            ]

        finally:
            db.close()

    @classmethod
    def get_for_user(
        cls,
        *,
        conversation_id: str,
        user_id: str,
    ) -> dict | None:
        db = SessionLocal()

        try:
            conversation = db.scalar(
                select(
                    Conversation
                ).where(
                    Conversation
                    .conversation_id
                    == conversation_id,
                    Conversation.user_id
                    == user_id,
                )
            )

            if conversation is None:
                return None

            messages = list(
                db.scalars(
                    select(
                        ConversationMessage
                    )
                    .where(
                        ConversationMessage
                        .conversation_id
                        == conversation_id,
                        ConversationMessage
                        .user_id
                        == user_id,
                    )
                    .order_by(
                        ConversationMessage
                        .created_at.asc(),
                        ConversationMessage
                        .id.asc(),
                    )
                ).all()
            )

            return {
                "conversation_id": (
                    conversation
                    .conversation_id
                ),
                "title": conversation.title,
                "created_at": (
                    conversation.created_at
                ),
                "updated_at": (
                    conversation.updated_at
                ),
                "messages": [
                    {
                        "message_id": (
                            message.message_id
                        ),
                        "role": (
                            message.role
                        ),
                        "content": (
                            message.content
                        ),
                        "route": (
                            message.route
                        ),
                        "document_ids": (
                            list(
                                message
                                .document_ids
                                or []
                            )
                        ),
                        "sources": list(
                            message.sources
                            or []
                        ),
                        "safety_category": (
                            message
                            .safety_category
                        ),
                        "created_at": (
                            message.created_at
                        ),
                    }
                    for message
                    in messages
                ],
            }

        finally:
            db.close()
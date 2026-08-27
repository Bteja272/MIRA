from datetime import datetime
from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


class ConversationMessageResponse(
    BaseModel
):
    model_config = ConfigDict(
        extra="forbid",
    )

    message_id: str
    role: str
    content: str

    route: str | None = None

    document_ids: list[str] = Field(
        default_factory=list,
    )

    sources: list[Any] = Field(
        default_factory=list,
    )

    safety_category: (
        str | None
    ) = None

    created_at: datetime


class ConversationSummaryResponse(
    BaseModel
):
    model_config = ConfigDict(
        extra="forbid",
    )

    conversation_id: str
    title: str
    message_count: int = Field(
        ge=0,
    )
    created_at: datetime
    updated_at: datetime


class ConversationListResponse(
    BaseModel
):
    model_config = ConfigDict(
        extra="forbid",
    )

    conversations: list[
        ConversationSummaryResponse
    ] = Field(
        default_factory=list,
    )


class ConversationDetailResponse(
    BaseModel
):
    model_config = ConfigDict(
        extra="forbid",
    )

    conversation_id: str
    title: str
    created_at: datetime
    updated_at: datetime

    messages: list[
        ConversationMessageResponse
    ] = Field(
        default_factory=list,
    )
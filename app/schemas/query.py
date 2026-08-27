from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


MAX_SELECTED_DOCUMENTS = 5


class QueryRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    query: str = Field(
        ...,
        min_length=1,
        max_length=4000,
    )

    document_id: str | None = None

    document_ids: (
        list[str] | None
    ) = None

    conversation_id: (
        str | None
    ) = Field(
        default=None,
        min_length=1,
        max_length=36,
    )

    @field_validator("query")
    @classmethod
    def clean_query(
        cls,
        value: str,
    ) -> str:
        cleaned = value.strip()

        if not cleaned:
            raise ValueError(
                "Query cannot be empty."
            )

        return cleaned

    @field_validator(
        "conversation_id"
    )
    @classmethod
    def clean_conversation_id(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        cleaned = value.strip()

        if not cleaned:
            return None

        return cleaned

    @model_validator(mode="after")
    def normalize_document_selection(
        self,
    ):
        selected_ids: list[str] = []
        candidates: list[str] = []

        if self.document_id:
            candidates.append(
                self.document_id
            )

        if self.document_ids:
            candidates.extend(
                self.document_ids
            )

        for candidate in candidates:
            cleaned = candidate.strip()

            if (
                cleaned
                and cleaned
                not in selected_ids
            ):
                selected_ids.append(
                    cleaned
                )

        if (
            len(selected_ids)
            > MAX_SELECTED_DOCUMENTS
        ):
            raise ValueError(
                "A maximum of "
                f"{MAX_SELECTED_DOCUMENTS} "
                "documents can be selected "
                "in one query."
            )

        self.document_ids = (
            selected_ids or None
        )

        return self


class QueryResponse(BaseModel):
    model_config = ConfigDict(
        extra="allow",
    )

    query: str
    answer: str | None = None
    route: str

    conversation_id: str
    message_id: str

    document_id: str | None = None

    document_ids: list[str] = Field(
        default_factory=list,
    )

    selected_document_count: int = Field(
        ge=0,
    )

    sources: list[Any] = Field(
        default_factory=list,
    )

    safety_category: (
        str | None
    ) = None
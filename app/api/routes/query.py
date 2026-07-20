from fastapi import APIRouter, HTTPException, status
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from app.services.document_service import DocumentService
from app.services.langgraph_agent_service import (
    LangGraphAgentService,
)


router = APIRouter(
    prefix="/query",
    tags=["query"],
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

    # Backward-compatible single-document field.
    document_id: str | None = None

    # Preferred field for one or multiple documents.
    document_ids: list[str] | None = None

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
                and cleaned not in selected_ids
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
                f"{MAX_SELECTED_DOCUMENTS} documents "
                "can be selected in one query."
            )

        self.document_ids = (
            selected_ids or None
        )

        return self


@router.post("")
def query_agent(
    request: QueryRequest,
) -> dict:
    selected_ids = (
        request.document_ids or []
    )

    if selected_ids:
        existing_ids = (
            DocumentService
            .get_existing_document_ids(
                document_ids=selected_ids,
                user_id=None,
            )
        )

        existing_id_set = set(
            existing_ids
        )

        missing_ids = [
            document_id
            for document_id in selected_ids
            if document_id
            not in existing_id_set
        ]

        if missing_ids:
            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail={
                    "message": (
                        "One or more selected "
                        "documents were not found."
                    ),
                    "missing_document_ids": (
                        missing_ids
                    ),
                },
            )

    # Critical: forward the normalized document list.
    return LangGraphAgentService.query(
        query=request.query,
        document_ids=selected_ids,
    )
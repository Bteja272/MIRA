from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


class DocumentSummary(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    document_id: str
    filename: str
    document_type: str | None = None
    file_size_bytes: int | None = Field(
        default=None,
        ge=0,
    )
    chunk_count: int = Field(
        ge=0,
    )
    uploaded_at: datetime | None = None


class DocumentDetail(
    DocumentSummary
):
    source: str | None = None
    file_hash: str | None = None


class DocumentListResponse(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    documents: list[DocumentSummary]
    count: int = Field(
        ge=0,
    )


class DocumentDeleteResponse(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    document_id: str
    filename: str
    deleted: bool
    file_deleted: bool
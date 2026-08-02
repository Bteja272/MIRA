from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


class IngestResponse(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    duplicate: bool

    document_id: str | None = None

    existing_document_id: (
        str | None
    ) = None

    filename: str
    document_type: str | None = None

    file_size_bytes: (
        int | None
    ) = Field(
        default=None,
        ge=0,
    )

    chunks_indexed: (
        int | None
    ) = Field(
        default=None,
        ge=0,
    )

    message: str

    development_notice: (
        str | None
    ) = None
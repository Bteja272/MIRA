from pydantic import (
    BaseModel,
    ConfigDict,
)

from app.schemas.extraction_persistence import (
    PersistedMedicalExtraction,
)


class ExtractionGenerateRequest(
    BaseModel
):
    model_config = ConfigDict(
        extra="forbid",
    )

    replace_existing: bool = False


class ExtractionGenerateResponse(
    BaseModel
):
    model_config = ConfigDict(
        extra="forbid",
    )

    cached: bool
    replaced: bool
    message: str
    result: PersistedMedicalExtraction


class ExtractionDeleteResponse(
    BaseModel
):
    model_config = ConfigDict(
        extra="forbid",
    )

    document_id: str
    deleted: bool
    message: str
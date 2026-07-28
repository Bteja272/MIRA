from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

from app.schemas.medical_extraction import (
    ExtractionMethod,
    ExtractionStatus,
    MedicalDocumentExtraction,
)


class PersistedMedicalExtraction(
    BaseModel
):
    model_config = ConfigDict(
        extra="forbid",
    )

    extraction_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
    )

    document_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
    )

    schema_version: str = Field(
        ...,
        min_length=1,
        max_length=20,
    )

    status: ExtractionStatus

    extraction_method: ExtractionMethod

    model_name: str = Field(
        ...,
        min_length=1,
        max_length=200,
    )

    extraction: (
        MedicalDocumentExtraction
    )

    created_at: datetime
    updated_at: datetime
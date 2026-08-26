from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

from app.schemas.medical_intelligence import (
    IntelligenceStatus,
    MedicalDocumentIntelligence,
)


class PersistedMedicalIntelligence(
    BaseModel
):
    model_config = ConfigDict(
        extra="forbid",
    )

    intelligence_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
    )

    document_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
    )

    source_extraction_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
    )

    source_extraction_updated_at: (
        datetime
    )

    schema_version: str = Field(
        ...,
        min_length=1,
        max_length=20,
    )

    status: IntelligenceStatus

    intelligence: (
        MedicalDocumentIntelligence
    )

    created_at: datetime
    updated_at: datetime
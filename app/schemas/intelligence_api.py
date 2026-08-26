from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

from app.schemas.intelligence_persistence import (
    PersistedMedicalIntelligence,
)
from app.schemas.medical_intelligence import (
    MedicalRecordChange,
    MedicalTimelineEvent,
)


MAX_INTELLIGENCE_DOCUMENTS = 5


class IntelligenceGenerateRequest(
    BaseModel
):
    model_config = ConfigDict(
        extra="forbid",
    )

    replace_existing: bool = False


class IntelligenceGenerateResponse(
    BaseModel
):
    model_config = ConfigDict(
        extra="forbid",
    )

    cached: bool
    replaced: bool
    extraction_generated: bool
    message: str
    result: PersistedMedicalIntelligence


class IntelligenceDeleteResponse(
    BaseModel
):
    model_config = ConfigDict(
        extra="forbid",
    )

    document_id: str
    deleted: bool
    message: str


class IntelligenceTimelineRequest(
    BaseModel
):
    model_config = ConfigDict(
        extra="forbid",
    )

    document_ids: list[str] = Field(
        ...,
        min_length=1,
        max_length=(
            MAX_INTELLIGENCE_DOCUMENTS
        ),
    )


class IntelligenceTimelineResponse(
    BaseModel
):
    model_config = ConfigDict(
        extra="forbid",
    )

    document_ids: list[str]

    events: list[
        MedicalTimelineEvent
    ]

    notices: list[str]

    generated_at: datetime


class IntelligenceCompareRequest(
    BaseModel
):
    model_config = ConfigDict(
        extra="forbid",
    )

    document_ids: list[str] = Field(
        ...,
        min_length=2,
        max_length=(
            MAX_INTELLIGENCE_DOCUMENTS
        ),
    )


class IntelligenceCompareResponse(
    BaseModel
):
    model_config = ConfigDict(
        extra="forbid",
    )

    document_ids: list[str]

    changes: list[
        MedicalRecordChange
    ]

    notices: list[str]

    generated_at: datetime
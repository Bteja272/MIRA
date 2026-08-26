from datetime import datetime
from enum import Enum
from typing import (
    Any,
    Literal,
)

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

from app.schemas.medical_extraction import (
    SourceEvidence,
)


class StrictIntelligenceSchema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_assignment=True,
    )


class IntelligenceStatus(
    str,
    Enum,
):
    COMPLETED = "completed"
    PARTIAL = "partial"


class MedicalEntityType(
    str,
    Enum,
):
    DIAGNOSIS = "diagnosis"
    MEDICATION = "medication"
    LAB = "lab"
    PROCEDURE = "procedure"
    PROVIDER = "provider"


class NormalizationMethod(
    str,
    Enum,
):
    EXACT = "exact"
    ALIAS = "alias"
    DOCUMENTED_CODE = "documented_code"


class GuidanceLevel(
    str,
    Enum,
):
    EDUCATION = "education"
    SUPPORTIVE = "supportive"
    URGENT_WARNING = "urgent_warning"


class TimelineEventType(
    str,
    Enum,
):
    DIAGNOSIS = "diagnosis"
    MEDICATION = "medication"
    LAB = "lab"
    PROCEDURE = "procedure"
    FOLLOW_UP = "follow_up"


class ChangeType(
    str,
    Enum,
):
    APPEARED = "appeared"
    NOT_MENTIONED_LATER = (
        "not_mentioned_later"
    )
    STATUS_CHANGED = "status_changed"
    VALUE_CHANGED = "value_changed"


class NormalizedMedicalEntity(
    StrictIntelligenceSchema
):
    entity_type: MedicalEntityType

    raw_name: str = Field(
        ...,
        min_length=1,
        max_length=500,
    )

    normalized_name: str = Field(
        ...,
        min_length=1,
        max_length=500,
    )

    canonical_key: str = Field(
        ...,
        min_length=1,
        max_length=600,
    )

    code: str | None = Field(
        default=None,
        max_length=100,
    )

    code_system: str | None = Field(
        default=None,
        max_length=100,
    )

    status: str | None = Field(
        default=None,
        max_length=100,
    )

    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
    )

    normalization_method: (
        NormalizationMethod
    )

    details: dict[
        str,
        Any,
    ] = Field(
        default_factory=dict,
    )

    sources: list[
        SourceEvidence
    ] = Field(
        default_factory=list,
    )


class DocumentedMedicalFact(
    StrictIntelligenceSchema
):
    category: str = Field(
        ...,
        min_length=1,
        max_length=100,
    )

    label: str = Field(
        ...,
        min_length=1,
        max_length=300,
    )

    value: str = Field(
        ...,
        min_length=1,
        max_length=2000,
    )

    sources: list[
        SourceEvidence
    ] = Field(
        default_factory=list,
    )


class MedicalGuidanceCard(
    StrictIntelligenceSchema
):
    topic: str = Field(
        ...,
        min_length=1,
        max_length=300,
    )

    documented_fact: (
        DocumentedMedicalFact
    )

    plain_language_explanation: str = (
        Field(
            ...,
            min_length=1,
            max_length=4000,
        )
    )

    general_information: list[
        str
    ] = Field(
        default_factory=list,
    )

    supportive_care: list[
        str
    ] = Field(
        default_factory=list,
    )

    red_flags: list[
        str
    ] = Field(
        default_factory=list,
    )

    when_to_seek_care: str | None = (
        Field(
            default=None,
            max_length=4000,
        )
    )

    questions_for_clinician: list[
        str
    ] = Field(
        default_factory=list,
    )

    guidance_level: GuidanceLevel

    safety_flags: list[
        str
    ] = Field(
        default_factory=list,
    )

    sources: list[
        SourceEvidence
    ] = Field(
        default_factory=list,
    )


class MedicalTimelineEvent(
    StrictIntelligenceSchema
):
    event_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
    )

    document_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
    )

    event_type: TimelineEventType

    title: str = Field(
        ...,
        min_length=1,
        max_length=500,
    )

    detail: str | None = Field(
        default=None,
        max_length=4000,
    )

    event_date: str | None = Field(
        default=None,
        max_length=100,
    )

    sources: list[
        SourceEvidence
    ] = Field(
        default_factory=list,
    )


class MedicalRecordChange(
    StrictIntelligenceSchema
):
    entity_type: MedicalEntityType

    canonical_key: str = Field(
        ...,
        min_length=1,
        max_length=600,
    )

    normalized_name: str = Field(
        ...,
        min_length=1,
        max_length=500,
    )

    change_type: ChangeType

    from_document_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
    )

    to_document_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
    )

    description: str = Field(
        ...,
        min_length=1,
        max_length=4000,
    )

    before_summary: str | None = (
        Field(
            default=None,
            max_length=2000,
        )
    )

    after_summary: str | None = (
        Field(
            default=None,
            max_length=2000,
        )
    )

    sources: list[
        SourceEvidence
    ] = Field(
        default_factory=list,
    )


class MedicalDocumentIntelligence(
    StrictIntelligenceSchema
):
    schema_version: Literal["1.0"] = "1.0"

    intelligence_id: str | None = Field(
        default=None,
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

    source_extraction_updated_at: datetime

    status: IntelligenceStatus

    normalized_entities: list[
        NormalizedMedicalEntity
    ] = Field(
        default_factory=list,
    )

    guidance_cards: list[
        MedicalGuidanceCard
    ] = Field(
        default_factory=list,
    )

    timeline_events: list[
        MedicalTimelineEvent
    ] = Field(
        default_factory=list,
    )

    warnings: list[
        str
    ] = Field(
        default_factory=list,
    )

    generated_at: datetime
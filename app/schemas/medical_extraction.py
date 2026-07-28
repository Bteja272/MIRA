from datetime import (
    date,
    datetime,
    timezone,
)
from enum import StrEnum
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)


class StrictSchema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_assignment=True,
    )


class MedicalDocumentType(StrEnum):
    LAB_REPORT = "lab_report"
    DISCHARGE_SUMMARY = "discharge_summary"
    PRESCRIPTION = "prescription"
    IMAGING_REPORT = "imaging_report"
    PATHOLOGY_REPORT = "pathology_report"
    VISIT_NOTE = "visit_note"
    VACCINATION_RECORD = "vaccination_record"
    INSURANCE_DOCUMENT = "insurance_document"
    UNKNOWN = "unknown"


class ExtractionStatus(StrEnum):
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"


class ExtractionMethod(StrEnum):
    DETERMINISTIC = "deterministic"
    LLM = "llm"
    HYBRID = "hybrid"


class LabResultFlag(StrEnum):
    HIGH = "high"
    LOW = "low"
    NORMAL = "normal"
    ABNORMAL = "abnormal"
    CRITICAL = "critical"
    POSITIVE = "positive"
    NEGATIVE = "negative"
    UNKNOWN = "unknown"


class MedicationStatus(StrEnum):
    CURRENT = "current"
    HISTORICAL = "historical"
    DISCONTINUED = "discontinued"
    AS_NEEDED = "as_needed"
    UNKNOWN = "unknown"


class DiagnosisStatus(StrEnum):
    ACTIVE = "active"
    RESOLVED = "resolved"
    HISTORICAL = "historical"
    RULED_OUT = "ruled_out"
    UNKNOWN = "unknown"


class SourceEvidence(StrictSchema):
    """
    Identifies the exact document location supporting an
    extracted medical fact.
    """

    document_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
    )

    chunk_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
    )

    source_filename: str | None = Field(
        default=None,
        min_length=1,
        max_length=500,
    )

    page_number: int | None = Field(
        default=None,
        ge=1,
    )

    chunk_index: int = Field(
        ...,
        ge=0,
    )

    quoted_text: str = Field(
        ...,
        min_length=1,
        max_length=3000,
    )


class SourcedTextValue(StrictSchema):
    """
    A text value that must include document evidence.
    """

    value: str = Field(
        ...,
        min_length=1,
        max_length=2000,
    )

    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
    )

    extraction_method: ExtractionMethod

    sources: list[SourceEvidence] = Field(
        ...,
        min_length=1,
    )


class SourcedDateValue(StrictSchema):
    """
    Preserves the exact date text from the document while
    optionally providing a normalized date.
    """

    raw_value: str = Field(
        ...,
        min_length=1,
        max_length=200,
    )

    normalized_value: date | None = None

    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
    )

    extraction_method: ExtractionMethod

    sources: list[SourceEvidence] = Field(
        ...,
        min_length=1,
    )


class PatientInformation(StrictSchema):
    name: SourcedTextValue | None = None
    date_of_birth: SourcedDateValue | None = None
    medical_record_number: SourcedTextValue | None = None


class ProviderInformation(StrictSchema):
    name: str = Field(
        ...,
        min_length=1,
        max_length=300,
    )

    role: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
    )

    organization: str | None = Field(
        default=None,
        min_length=1,
        max_length=300,
    )

    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
    )

    extraction_method: ExtractionMethod

    sources: list[SourceEvidence] = Field(
        ...,
        min_length=1,
    )


class DiagnosisInformation(StrictSchema):
    name: str = Field(
        ...,
        min_length=1,
        max_length=500,
    )

    code: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    code_system: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    status: DiagnosisStatus = (
        DiagnosisStatus.UNKNOWN
    )

    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
    )

    extraction_method: ExtractionMethod

    sources: list[SourceEvidence] = Field(
        ...,
        min_length=1,
    )


class MedicationInformation(StrictSchema):
    name: str = Field(
        ...,
        min_length=1,
        max_length=500,
    )

    dose: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
    )

    route: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
    )

    frequency: str | None = Field(
        default=None,
        min_length=1,
        max_length=300,
    )

    duration: str | None = Field(
        default=None,
        min_length=1,
        max_length=300,
    )

    instructions: str | None = Field(
        default=None,
        min_length=1,
        max_length=1000,
    )

    status: MedicationStatus = (
        MedicationStatus.UNKNOWN
    )

    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
    )

    extraction_method: ExtractionMethod

    sources: list[SourceEvidence] = Field(
        ...,
        min_length=1,
    )


class LabResultInformation(StrictSchema):
    test_name: str = Field(
        ...,
        min_length=1,
        max_length=500,
    )

    raw_value: str = Field(
        ...,
        min_length=1,
        max_length=300,
    )

    numeric_value: float | None = None

    unit: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    reference_range: str | None = Field(
        default=None,
        min_length=1,
        max_length=300,
    )

    flag: LabResultFlag = (
        LabResultFlag.UNKNOWN
    )

    collected_at: SourcedDateValue | None = None

    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
    )

    extraction_method: ExtractionMethod

    sources: list[SourceEvidence] = Field(
        ...,
        min_length=1,
    )


class ProcedureInformation(StrictSchema):
    name: str = Field(
        ...,
        min_length=1,
        max_length=500,
    )

    procedure_date: SourcedDateValue | None = None

    result: str | None = Field(
        default=None,
        min_length=1,
        max_length=2000,
    )

    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
    )

    extraction_method: ExtractionMethod

    sources: list[SourceEvidence] = Field(
        ...,
        min_length=1,
    )


class FollowUpInstruction(StrictSchema):
    instruction: str = Field(
        ...,
        min_length=1,
        max_length=2000,
    )

    timeframe: str | None = Field(
        default=None,
        min_length=1,
        max_length=300,
    )

    specialty: str | None = Field(
        default=None,
        min_length=1,
        max_length=300,
    )

    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
    )

    extraction_method: ExtractionMethod

    sources: list[SourceEvidence] = Field(
        ...,
        min_length=1,
    )


class ExtractionWarning(StrictSchema):
    code: str = Field(
        ...,
        min_length=1,
        max_length=100,
    )

    message: str = Field(
        ...,
        min_length=1,
        max_length=1000,
    )


class MedicalDocumentExtraction(StrictSchema):
    schema_version: Literal["1.0"] = "1.0"

    extraction_id: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    document_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
    )

    document_type: MedicalDocumentType

    status: ExtractionStatus = (
        ExtractionStatus.COMPLETED
    )

    patient: PatientInformation = Field(
        default_factory=PatientInformation
    )

    document_date: SourcedDateValue | None = None

    providers: list[ProviderInformation] = Field(
        default_factory=list
    )

    diagnoses: list[DiagnosisInformation] = Field(
        default_factory=list
    )

    medications: list[MedicationInformation] = Field(
        default_factory=list
    )

    lab_results: list[LabResultInformation] = Field(
        default_factory=list
    )

    procedures: list[ProcedureInformation] = Field(
        default_factory=list
    )

    follow_up_instructions: list[
        FollowUpInstruction
    ] = Field(
        default_factory=list
    )

    warnings: list[ExtractionWarning] = Field(
        default_factory=list
    )

    extraction_confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
    )

    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc
        )
    )

    @model_validator(mode="after")
    def validate_source_ownership(
        self,
    ):
        """
        Ensure that every evidence reference belongs to the
        document being extracted.

        This prevents an extraction from accidentally citing a
        chunk belonging to another document or user.
        """
        evidence_groups: list[
            list[SourceEvidence]
        ] = []

        patient_values = (
            self.patient.name,
            self.patient.date_of_birth,
            self.patient.medical_record_number,
        )

        for patient_value in patient_values:
            if patient_value is not None:
                evidence_groups.append(
                    patient_value.sources
                )

        if self.document_date is not None:
            evidence_groups.append(
                self.document_date.sources
            )

        for provider in self.providers:
            evidence_groups.append(
                provider.sources
            )

        for diagnosis in self.diagnoses:
            evidence_groups.append(
                diagnosis.sources
            )

        for medication in self.medications:
            evidence_groups.append(
                medication.sources
            )

        for lab_result in self.lab_results:
            evidence_groups.append(
                lab_result.sources
            )

            if (
                lab_result.collected_at
                is not None
            ):
                evidence_groups.append(
                    lab_result
                    .collected_at
                    .sources
                )

        for procedure in self.procedures:
            evidence_groups.append(
                procedure.sources
            )

            if (
                procedure.procedure_date
                is not None
            ):
                evidence_groups.append(
                    procedure
                    .procedure_date
                    .sources
                )

        for instruction in (
            self.follow_up_instructions
        ):
            evidence_groups.append(
                instruction.sources
            )

        for evidence_group in evidence_groups:
            for source in evidence_group:
                if (
                    source.document_id
                    != self.document_id
                ):
                    raise ValueError(
                        "Every source must belong "
                        "to the extracted document."
                    )

        return self
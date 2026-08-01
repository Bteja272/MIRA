from __future__ import annotations

from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from app.schemas.medical_extraction import (
    DiagnosisStatus,
    LabResultFlag,
    MedicationStatus,
)


MAX_CANDIDATES_PER_CATEGORY = 50
PLACEHOLDER_VALUES = {
    "",
    "null",
    "none",
    "n/a",
    "na",
    "unknown",
    "not available",
    "not provided",
}


def _unwrap_fact_value(value: Any) -> Any:
    if isinstance(value, dict):
        return (
            value.get("raw_value")
            or value.get("value")
        )

    return value


def _clean_text(
    value: Any,
    *,
    allow_numbers: bool = False,
) -> str | None:
    value = _unwrap_fact_value(value)

    if isinstance(value, str):
        cleaned = value.strip()

        if cleaned.casefold() in PLACEHOLDER_VALUES:
            return None

        return cleaned or None

    if (
        allow_numbers
        and isinstance(value, (int, float))
        and not isinstance(value, bool)
    ):
        return str(value)

    return None


def _as_candidate_list(value: Any) -> list[Any]:
    if value is None:
        return []

    if isinstance(value, list):
        return value[:MAX_CANDIDATES_PER_CATEGORY]

    if isinstance(value, dict):
        return [value]

    return []


class CandidateSchema(BaseModel):
    """
    Lightweight schema for untrusted LLM candidate facts.

    The model cannot control trusted metadata, confidence scores,
    extraction methods, or evidence. Extra fields are ignored and the
    server builds trusted objects after verifying each candidate against
    the original document text.
    """

    model_config = ConfigDict(
        extra="ignore",
        str_strip_whitespace=True,
    )


class CandidatePatientInformation(CandidateSchema):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=500,
    )

    date_of_birth: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
    )

    medical_record_number: str | None = Field(
        default=None,
        min_length=1,
        max_length=300,
    )

    @field_validator(
        "name",
        "date_of_birth",
        "medical_record_number",
        mode="before",
    )
    @classmethod
    def normalize_optional_fact(
        cls,
        value: Any,
    ) -> str | None:
        return _clean_text(
            value,
            allow_numbers=True,
        )


class CandidateProviderInformation(CandidateSchema):
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


class CandidateDiagnosisInformation(CandidateSchema):
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


class CandidateMedicationInformation(CandidateSchema):
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


class CandidateLabResultInformation(CandidateSchema):
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

    collected_at: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
    )


class CandidateProcedureInformation(CandidateSchema):
    name: str = Field(
        ...,
        min_length=1,
        max_length=500,
    )

    procedure_date: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
    )

    result: str | None = Field(
        default=None,
        min_length=1,
        max_length=2000,
    )


class CandidateFollowUpInstruction(CandidateSchema):
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


class MedicalExtractionCandidate(CandidateSchema):
    patient: CandidatePatientInformation = Field(
        default_factory=CandidatePatientInformation
    )

    document_date: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
    )

    providers: list[
        CandidateProviderInformation
    ] = Field(default_factory=list)

    diagnoses: list[
        CandidateDiagnosisInformation
    ] = Field(default_factory=list)

    medications: list[
        CandidateMedicationInformation
    ] = Field(default_factory=list)

    lab_results: list[
        CandidateLabResultInformation
    ] = Field(default_factory=list)

    procedures: list[
        CandidateProcedureInformation
    ] = Field(default_factory=list)

    follow_up_instructions: list[
        CandidateFollowUpInstruction
    ] = Field(default_factory=list)

    @staticmethod
    def _clean_optional_fields(
        item: dict[str, Any],
        field_names: tuple[str, ...],
    ) -> dict[str, Any]:
        cleaned = dict(item)

        for field_name in field_names:
            cleaned[field_name] = _clean_text(
                cleaned.get(field_name),
                allow_numbers=True,
            )

        return cleaned

    @staticmethod
    def _normalize_enum_value(
        value: Any,
        allowed_values: set[str],
    ) -> str:
        cleaned = _clean_text(value)

        if cleaned is None:
            return "unknown"

        normalized = cleaned.casefold()

        if normalized not in allowed_values:
            return "unknown"

        return normalized

    @classmethod
    def _sanitize_named_items(
        cls,
        value: Any,
        *,
        optional_fields: tuple[str, ...],
        enum_field: str | None = None,
        enum_values: set[str] | None = None,
    ) -> list[dict[str, Any]]:
        sanitized: list[dict[str, Any]] = []

        for item in _as_candidate_list(value):
            if not isinstance(item, dict):
                continue

            cleaned = cls._clean_optional_fields(
                item,
                ("name", *optional_fields),
            )

            if cleaned.get("name") is None:
                continue

            if enum_field is not None:
                cleaned[enum_field] = (
                    cls._normalize_enum_value(
                        cleaned.get(enum_field),
                        enum_values or set(),
                    )
                )

            sanitized.append(cleaned)

        return sanitized

    @model_validator(mode="before")
    @classmethod
    def sanitize_placeholder_output(
        cls,
        value: Any,
    ) -> Any:
        """
        Remove placeholder rows such as {"name": null} and
        {"test_name": null, "raw_value": null}.

        Local models frequently emit one null-filled object instead of an
        empty array. Those objects represent absence, not invalid medical
        facts, so they are discarded before strict candidate validation.
        """
        if not isinstance(value, dict):
            return value

        payload = dict(value)

        patient = payload.get("patient")
        if not isinstance(patient, dict):
            patient = {}

        payload["patient"] = {
            "name": _clean_text(
                patient.get("name"),
                allow_numbers=True,
            ),
            "date_of_birth": _clean_text(
                patient.get("date_of_birth"),
                allow_numbers=True,
            ),
            "medical_record_number": _clean_text(
                patient.get("medical_record_number"),
                allow_numbers=True,
            ),
        }

        payload["document_date"] = _clean_text(
            payload.get("document_date"),
            allow_numbers=True,
        )

        payload["providers"] = (
            cls._sanitize_named_items(
                payload.get("providers"),
                optional_fields=(
                    "role",
                    "organization",
                ),
            )
        )

        payload["diagnoses"] = (
            cls._sanitize_named_items(
                payload.get("diagnoses"),
                optional_fields=(
                    "code",
                    "code_system",
                ),
                enum_field="status",
                enum_values={
                    item.value
                    for item in DiagnosisStatus
                },
            )
        )

        payload["medications"] = (
            cls._sanitize_named_items(
                payload.get("medications"),
                optional_fields=(
                    "dose",
                    "route",
                    "frequency",
                    "duration",
                    "instructions",
                ),
                enum_field="status",
                enum_values={
                    item.value
                    for item in MedicationStatus
                },
            )
        )

        sanitized_labs: list[
            dict[str, Any]
        ] = []

        for item in _as_candidate_list(
            payload.get("lab_results")
        ):
            if not isinstance(item, dict):
                continue

            cleaned = cls._clean_optional_fields(
                item,
                (
                    "test_name",
                    "raw_value",
                    "unit",
                    "reference_range",
                    "collected_at",
                ),
            )

            if (
                cleaned.get("test_name") is None
                or cleaned.get("raw_value") is None
            ):
                continue

            cleaned["flag"] = (
                cls._normalize_enum_value(
                    cleaned.get("flag"),
                    {
                        item.value
                        for item in LabResultFlag
                    },
                )
            )

            sanitized_labs.append(cleaned)

        payload["lab_results"] = (
            sanitized_labs
        )

        payload["procedures"] = (
            cls._sanitize_named_items(
                payload.get("procedures"),
                optional_fields=(
                    "procedure_date",
                    "result",
                ),
            )
        )

        sanitized_follow_up: list[
            dict[str, Any]
        ] = []

        for item in _as_candidate_list(
            payload.get(
                "follow_up_instructions"
            )
        ):
            if not isinstance(item, dict):
                continue

            cleaned = cls._clean_optional_fields(
                item,
                (
                    "instruction",
                    "timeframe",
                    "specialty",
                ),
            )

            if cleaned.get("instruction") is None:
                continue

            sanitized_follow_up.append(cleaned)

        payload["follow_up_instructions"] = (
            sanitized_follow_up
        )

        return payload
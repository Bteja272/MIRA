from __future__ import annotations

import re
from collections.abc import Callable, Iterable
from typing import Any, TypeVar

from app.schemas.medical_extraction import (
    DiagnosisInformation,
    ExtractionStatus,
    ExtractionWarning,
    FollowUpInstruction,
    LabResultFlag,
    LabResultInformation,
    MedicalDocumentExtraction,
    MedicationInformation,
    ProcedureInformation,
    ProviderInformation,
    SourceEvidence,
    SourcedDateValue,
    SourcedTextValue,
)


ExtractionItem = TypeVar("ExtractionItem")


class MedicalExtractionHardeningError(ValueError):
    pass


class MedicalExtractionHardeningService:
    """
    Apply final safety checks to a merged medical extraction.

    This service does not trust the LLM's confidence, status, or optional
    fields. It verifies that extracted values are supported by the exact
    source quotes, removes duplicates, and calculates one aggregate
    confidence value from the facts that survived validation.
    """

    ROUTE_ALIASES: dict[str, tuple[str, ...]] = {
        "oral": ("oral", "orally", "by mouth", "po"),
        "intravenous": ("intravenous", "intravenously", "iv"),
        "intramuscular": ("intramuscular", "intramuscularly", "im"),
        "subcutaneous": ("subcutaneous", "subcutaneously", "subq", "sq"),
        "topical": ("topical", "topically"),
        "inhaled": ("inhaled", "inhalation"),
    }

    FREQUENCY_ALIASES: dict[str, tuple[str, ...]] = {
        "daily": ("daily", "once daily", "qd"),
        "once daily": ("once daily", "daily", "qd"),
        "twice daily": ("twice daily", "bid"),
        "three times daily": ("three times daily", "tid"),
        "nightly": ("nightly", "qhs", "at bedtime"),
        "as needed": ("as needed", "prn"),
    }

    @staticmethod
    def _normalize(value: str | None) -> str:
        if not value:
            return ""

        normalized = value.casefold()
        normalized = re.sub(r"[^a-z0-9]+", " ", normalized)
        return " ".join(normalized.split())

    @classmethod
    def _quote_text(
        cls,
        sources: Iterable[SourceEvidence],
    ) -> str:
        return "\n".join(
            source.quoted_text
            for source in sources
            if source.quoted_text
        )

    @classmethod
    def _supported(
        cls,
        value: str | None,
        quote: str,
        *,
        aliases: tuple[str, ...] = (),
    ) -> bool:
        if value is None:
            return True

        normalized_quote = cls._normalize(quote)
        normalized_value = cls._normalize(value)

        if not normalized_value:
            return False

        if normalized_value in normalized_quote:
            return True

        for alias in aliases:
            normalized_alias = cls._normalize(alias)

            if (
                normalized_alias
                and normalized_alias in normalized_quote
            ):
                return True

        return False

    @classmethod
    def _aliases_for(
        cls,
        value: str | None,
        alias_map: dict[str, tuple[str, ...]],
    ) -> tuple[str, ...]:
        normalized_value = cls._normalize(value)

        for canonical, aliases in alias_map.items():
            normalized_options = {
                cls._normalize(canonical),
                *(
                    cls._normalize(alias)
                    for alias in aliases
                ),
            }

            if normalized_value in normalized_options:
                return aliases

        return ()

    @classmethod
    def _require_supported(
        cls,
        *,
        field_name: str,
        value: str | None,
        sources: Iterable[SourceEvidence],
        aliases: tuple[str, ...] = (),
    ) -> None:
        if value is None:
            return

        quote = cls._quote_text(sources)

        if not cls._supported(
            value,
            quote,
            aliases=aliases,
        ):
            raise MedicalExtractionHardeningError(
                f"The extracted {field_name} is not supported by its "
                "source evidence."
            )

    @classmethod
    def _validate_sourced_text(
        cls,
        value: SourcedTextValue | None,
        field_name: str,
    ) -> None:
        if value is None:
            return

        cls._require_supported(
            field_name=field_name,
            value=value.value,
            sources=value.sources,
        )

    @classmethod
    def _validate_sourced_date(
        cls,
        value: SourcedDateValue | None,
        field_name: str,
    ) -> None:
        if value is None:
            return

        cls._require_supported(
            field_name=field_name,
            value=value.raw_value,
            sources=value.sources,
        )

    @classmethod
    def _validate_provider(
        cls,
        provider: ProviderInformation,
    ) -> None:
        cls._require_supported(
            field_name="provider name",
            value=provider.name,
            sources=provider.sources,
        )
        cls._require_supported(
            field_name="provider role",
            value=provider.role,
            sources=provider.sources,
        )
        cls._require_supported(
            field_name="provider organization",
            value=provider.organization,
            sources=provider.sources,
        )

    @classmethod
    def _validate_diagnosis(
        cls,
        diagnosis: DiagnosisInformation,
    ) -> None:
        cls._require_supported(
            field_name="diagnosis name",
            value=diagnosis.name,
            sources=diagnosis.sources,
        )
        cls._require_supported(
            field_name="diagnosis code",
            value=diagnosis.code,
            sources=diagnosis.sources,
        )
        cls._require_supported(
            field_name="diagnosis code system",
            value=diagnosis.code_system,
            sources=diagnosis.sources,
        )

    @classmethod
    def _validate_medication(
        cls,
        medication: MedicationInformation,
    ) -> None:
        route_aliases = cls._aliases_for(
            medication.route,
            cls.ROUTE_ALIASES,
        )
        frequency_aliases = cls._aliases_for(
            medication.frequency,
            cls.FREQUENCY_ALIASES,
        )

        cls._require_supported(
            field_name="medication name",
            value=medication.name,
            sources=medication.sources,
        )
        cls._require_supported(
            field_name="medication dose",
            value=medication.dose,
            sources=medication.sources,
        )
        cls._require_supported(
            field_name="medication route",
            value=medication.route,
            sources=medication.sources,
            aliases=route_aliases,
        )
        cls._require_supported(
            field_name="medication frequency",
            value=medication.frequency,
            sources=medication.sources,
            aliases=frequency_aliases,
        )
        cls._require_supported(
            field_name="medication duration",
            value=medication.duration,
            sources=medication.sources,
        )
        cls._require_supported(
            field_name="medication instructions",
            value=medication.instructions,
            sources=medication.sources,
        )

    @classmethod
    def _validate_lab_flag(
        cls,
        lab_result: LabResultInformation,
    ) -> None:
        if lab_result.flag == LabResultFlag.UNKNOWN:
            return

        quote = cls._normalize(
            cls._quote_text(lab_result.sources)
        )
        raw_value = cls._normalize(
            lab_result.raw_value
        )

        if (
            lab_result.flag == LabResultFlag.POSITIVE
            and raw_value == "positive"
        ):
            return

        if (
            lab_result.flag == LabResultFlag.NEGATIVE
            and raw_value == "negative"
        ):
            return

        if cls._normalize(lab_result.flag.value) in quote:
            return

        if (
            lab_result.flag == LabResultFlag.HIGH
            and re.search(r"(?:^|\s)h(?:\s|$)", quote)
        ):
            return

        if (
            lab_result.flag == LabResultFlag.LOW
            and re.search(r"(?:^|\s)l(?:\s|$)", quote)
        ):
            return

        raise MedicalExtractionHardeningError(
            "The extracted lab flag is not supported by its source "
            "evidence."
        )

    @classmethod
    def _validate_lab_result(
        cls,
        lab_result: LabResultInformation,
    ) -> None:
        cls._require_supported(
            field_name="lab test name",
            value=lab_result.test_name,
            sources=lab_result.sources,
        )
        cls._require_supported(
            field_name="lab raw value",
            value=lab_result.raw_value,
            sources=lab_result.sources,
        )
        cls._require_supported(
            field_name="lab unit",
            value=lab_result.unit,
            sources=lab_result.sources,
        )
        cls._require_supported(
            field_name="lab reference range",
            value=lab_result.reference_range,
            sources=lab_result.sources,
        )
        cls._validate_lab_flag(lab_result)
        cls._validate_sourced_date(
            lab_result.collected_at,
            "lab collection date",
        )

    @classmethod
    def _validate_procedure(
        cls,
        procedure: ProcedureInformation,
    ) -> None:
        cls._require_supported(
            field_name="procedure name",
            value=procedure.name,
            sources=procedure.sources,
        )
        cls._require_supported(
            field_name="procedure result",
            value=procedure.result,
            sources=procedure.sources,
        )
        cls._validate_sourced_date(
            procedure.procedure_date,
            "procedure date",
        )

    @classmethod
    def _validate_follow_up(
        cls,
        instruction: FollowUpInstruction,
    ) -> None:
        cls._require_supported(
            field_name="follow-up instruction",
            value=instruction.instruction,
            sources=instruction.sources,
        )
        cls._require_supported(
            field_name="follow-up timeframe",
            value=instruction.timeframe,
            sources=instruction.sources,
        )
        cls._require_supported(
            field_name="follow-up specialty",
            value=instruction.specialty,
            sources=instruction.sources,
        )

    @classmethod
    def validate_fact_support(
        cls,
        extraction: MedicalDocumentExtraction,
    ) -> None:
        cls._validate_sourced_text(
            extraction.patient.name,
            "patient name",
        )
        cls._validate_sourced_date(
            extraction.patient.date_of_birth,
            "patient date of birth",
        )
        cls._validate_sourced_text(
            extraction.patient.medical_record_number,
            "medical record number",
        )
        cls._validate_sourced_date(
            extraction.document_date,
            "document date",
        )

        for provider in extraction.providers:
            cls._validate_provider(provider)

        for diagnosis in extraction.diagnoses:
            cls._validate_diagnosis(diagnosis)

        for medication in extraction.medications:
            cls._validate_medication(medication)

        for lab_result in extraction.lab_results:
            cls._validate_lab_result(lab_result)

        for procedure in extraction.procedures:
            cls._validate_procedure(procedure)

        for instruction in extraction.follow_up_instructions:
            cls._validate_follow_up(instruction)

    @classmethod
    def _deduplicate(
        cls,
        items: list[ExtractionItem],
        key_builder: Callable[[ExtractionItem], Any],
    ) -> tuple[list[ExtractionItem], int]:
        unique_items: list[ExtractionItem] = []
        seen: set[Any] = set()
        removed = 0

        for item in items:
            key = key_builder(item)

            if key in seen:
                removed += 1
                continue

            seen.add(key)
            unique_items.append(item)

        return unique_items, removed

    @classmethod
    def _provider_key(
        cls,
        item: ProviderInformation,
    ) -> tuple[str, str, str]:
        return (
            cls._normalize(item.name),
            cls._normalize(item.role),
            cls._normalize(item.organization),
        )

    @classmethod
    def _diagnosis_key(
        cls,
        item: DiagnosisInformation,
    ) -> tuple[str, str]:
        return (
            cls._normalize(item.name),
            cls._normalize(item.code),
        )

    @classmethod
    def _medication_key(
        cls,
        item: MedicationInformation,
    ) -> tuple[str, str]:
        return (
            cls._normalize(item.name),
            cls._normalize(item.dose),
        )

    @classmethod
    def _lab_key(
        cls,
        item: LabResultInformation,
    ) -> tuple[str, str, str]:
        return (
            cls._normalize(item.test_name),
            cls._normalize(item.raw_value),
            cls._normalize(item.unit),
        )

    @classmethod
    def _procedure_key(
        cls,
        item: ProcedureInformation,
    ) -> tuple[str, str]:
        procedure_date = (
            item.procedure_date.raw_value
            if item.procedure_date is not None
            else ""
        )

        return (
            cls._normalize(item.name),
            cls._normalize(procedure_date),
        )

    @classmethod
    def _follow_up_key(
        cls,
        item: FollowUpInstruction,
    ) -> str:
        return cls._normalize(item.instruction)

    @staticmethod
    def _warning_key(
        warning: ExtractionWarning,
    ) -> tuple[str, str]:
        return warning.code, warning.message

    @staticmethod
    def _fact_confidences(
        extraction: MedicalDocumentExtraction,
    ) -> list[float]:
        values: list[float] = []

        for patient_value in (
            extraction.patient.name,
            extraction.patient.date_of_birth,
            extraction.patient.medical_record_number,
        ):
            if patient_value is not None:
                values.append(patient_value.confidence)

        if extraction.document_date is not None:
            values.append(
                extraction.document_date.confidence
            )

        for collection in (
            extraction.providers,
            extraction.diagnoses,
            extraction.medications,
            extraction.lab_results,
            extraction.procedures,
            extraction.follow_up_instructions,
        ):
            values.extend(
                item.confidence
                for item in collection
            )

        for lab_result in extraction.lab_results:
            if lab_result.collected_at is not None:
                values.append(
                    lab_result.collected_at.confidence
                )

        for procedure in extraction.procedures:
            if procedure.procedure_date is not None:
                values.append(
                    procedure.procedure_date.confidence
                )

        return values

    @classmethod
    def finalize(
        cls,
        extraction: MedicalDocumentExtraction,
    ) -> MedicalDocumentExtraction:
        providers, provider_duplicates = cls._deduplicate(
            extraction.providers,
            cls._provider_key,
        )
        diagnoses, diagnosis_duplicates = cls._deduplicate(
            extraction.diagnoses,
            cls._diagnosis_key,
        )
        medications, medication_duplicates = cls._deduplicate(
            extraction.medications,
            cls._medication_key,
        )
        lab_results, lab_duplicates = cls._deduplicate(
            extraction.lab_results,
            cls._lab_key,
        )
        procedures, procedure_duplicates = cls._deduplicate(
            extraction.procedures,
            cls._procedure_key,
        )
        follow_up, follow_up_duplicates = cls._deduplicate(
            extraction.follow_up_instructions,
            cls._follow_up_key,
        )
        warnings, _ = cls._deduplicate(
            extraction.warnings,
            cls._warning_key,
        )

        duplicate_count = sum(
            (
                provider_duplicates,
                diagnosis_duplicates,
                medication_duplicates,
                lab_duplicates,
                procedure_duplicates,
                follow_up_duplicates,
            )
        )

        if duplicate_count:
            warnings.append(
                ExtractionWarning(
                    code="duplicate_facts_removed",
                    message=(
                        f"{duplicate_count} duplicate extracted fact(s) "
                        "were removed."
                    ),
                )
            )

        payload = extraction.model_dump(
            mode="python"
        )
        payload.update(
            {
                "providers": providers,
                "diagnoses": diagnoses,
                "medications": medications,
                "lab_results": lab_results,
                "procedures": procedures,
                "follow_up_instructions": follow_up,
                "warnings": warnings,
            }
        )

        hardened = (
            MedicalDocumentExtraction
            .model_validate(payload)
        )

        cls.validate_fact_support(hardened)

        confidence_values = cls._fact_confidences(
            hardened
        )
        aggregate_confidence = (
            round(
                sum(confidence_values)
                / len(confidence_values),
                3,
            )
            if confidence_values
            else 0.0
        )

        status = (
            ExtractionStatus.PARTIAL
            if hardened.warnings
            or not confidence_values
            else ExtractionStatus.COMPLETED
        )

        return hardened.model_copy(
            update={
                "status": status,
                "extraction_confidence": (
                    aggregate_confidence
                ),
            }
        )
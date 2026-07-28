from collections.abc import (
    Callable,
)
from typing import (
    Any,
    TypeVar,
)

from app.schemas.medical_extraction import (
    ExtractionStatus,
    MedicalDocumentExtraction,
)


ExtractionItem = TypeVar(
    "ExtractionItem"
)


class MedicalExtractionMergeService:
    """
    Merge deterministic and LLM extraction results.

    Deterministic facts are placed first and win when both
    extraction paths produce the same normalized fact.
    """

    @staticmethod
    def _normalize(
        value: str | None,
    ) -> str:
        return " ".join(
            (value or "")
            .casefold()
            .split()
        )

    @classmethod
    def _merge_unique(
        cls,
        primary_items: list[
            ExtractionItem
        ],
        secondary_items: list[
            ExtractionItem
        ],
        key_builder: Callable[
            [ExtractionItem],
            Any,
        ],
    ) -> list[ExtractionItem]:
        merged: list[
            ExtractionItem
        ] = []

        seen_keys: set[Any] = set()

        for item in [
            *primary_items,
            *secondary_items,
        ]:
            key = key_builder(item)

            if key in seen_keys:
                continue

            seen_keys.add(key)
            merged.append(item)

        return merged

    @classmethod
    def _lab_key(
        cls,
        item,
    ) -> tuple[str, str, str]:
        return (
            cls._normalize(
                item.test_name
            ),
            cls._normalize(
                item.raw_value
            ),
            cls._normalize(
                item.unit
            ),
        )

    @classmethod
    def _medication_key(
        cls,
        item,
    ) -> tuple[str, str]:
        return (
            cls._normalize(
                item.name
            ),
            cls._normalize(
                item.dose
            ),
        )

    @classmethod
    def _provider_key(
        cls,
        item,
    ) -> tuple[str, str, str]:
        return (
            cls._normalize(
                item.name
            ),
            cls._normalize(
                item.role
            ),
            cls._normalize(
                item.organization
            ),
        )

    @classmethod
    def _diagnosis_key(
        cls,
        item,
    ) -> tuple[str, str]:
        return (
            cls._normalize(
                item.name
            ),
            cls._normalize(
                item.code
            ),
        )

    @classmethod
    def _procedure_key(
        cls,
        item,
    ) -> tuple[str, str]:
        procedure_date = ""

        if (
            item.procedure_date
            is not None
        ):
            procedure_date = (
                item.procedure_date
                .raw_value
            )

        return (
            cls._normalize(
                item.name
            ),
            cls._normalize(
                procedure_date
            ),
        )

    @classmethod
    def _follow_up_key(
        cls,
        item,
    ) -> str:
        return cls._normalize(
            item.instruction
        )

    @staticmethod
    def _warning_key(
        warning,
    ) -> tuple[str, str]:
        return (
            warning.code,
            warning.message,
        )

    @classmethod
    def merge(
        cls,
        deterministic: (
            MedicalDocumentExtraction
        ),
        llm: MedicalDocumentExtraction,
    ) -> MedicalDocumentExtraction:
        if (
            deterministic.document_id
            != llm.document_id
        ):
            raise ValueError(
                "Extraction document IDs "
                "do not match."
            )

        patient_payload = (
            llm.patient.model_dump(
                mode="python"
            )
        )

        for field_name in (
            "name",
            "date_of_birth",
            "medical_record_number",
        ):
            deterministic_value = (
                getattr(
                    deterministic.patient,
                    field_name,
                )
            )

            if (
                deterministic_value
                is not None
            ):
                patient_payload[
                    field_name
                ] = (
                    deterministic_value
                    .model_dump(
                        mode="python"
                    )
                )

        providers = (
            cls._merge_unique(
                primary_items=(
                    deterministic.providers
                ),
                secondary_items=(
                    llm.providers
                ),
                key_builder=(
                    cls._provider_key
                ),
            )
        )

        diagnoses = (
            cls._merge_unique(
                primary_items=(
                    deterministic.diagnoses
                ),
                secondary_items=(
                    llm.diagnoses
                ),
                key_builder=(
                    cls._diagnosis_key
                ),
            )
        )

        medications = (
            cls._merge_unique(
                primary_items=(
                    deterministic.medications
                ),
                secondary_items=(
                    llm.medications
                ),
                key_builder=(
                    cls._medication_key
                ),
            )
        )

        lab_results = (
            cls._merge_unique(
                primary_items=(
                    deterministic.lab_results
                ),
                secondary_items=(
                    llm.lab_results
                ),
                key_builder=(
                    cls._lab_key
                ),
            )
        )

        procedures = (
            cls._merge_unique(
                primary_items=(
                    deterministic.procedures
                ),
                secondary_items=(
                    llm.procedures
                ),
                key_builder=(
                    cls._procedure_key
                ),
            )
        )

        follow_up_instructions = (
            cls._merge_unique(
                primary_items=(
                    deterministic
                    .follow_up_instructions
                ),
                secondary_items=(
                    llm
                    .follow_up_instructions
                ),
                key_builder=(
                    cls._follow_up_key
                ),
            )
        )

        warnings = (
            cls._merge_unique(
                primary_items=(
                    deterministic.warnings
                ),
                secondary_items=(
                    llm.warnings
                ),
                key_builder=(
                    cls._warning_key
                ),
            )
        )

        status = llm.status

        if (
            status
            == ExtractionStatus.FAILED
        ):
            status = (
                ExtractionStatus.PARTIAL
            )

        payload = (
            llm.model_dump(
                mode="python"
            )
        )

        payload.update(
            {
                "document_id": (
                    deterministic
                    .document_id
                ),
                "document_type": (
                    deterministic
                    .document_type
                ),
                "status": status,
                "patient": (
                    patient_payload
                ),
                "document_date": (
                    deterministic
                    .document_date
                    if deterministic
                    .document_date
                    is not None
                    else llm.document_date
                ),
                "providers": providers,
                "diagnoses": diagnoses,
                "medications": medications,
                "lab_results": lab_results,
                "procedures": procedures,
                "follow_up_instructions": (
                    follow_up_instructions
                ),
                "warnings": warnings,
                "extraction_confidence": (
                    max(
                        deterministic
                        .extraction_confidence,
                        llm
                        .extraction_confidence,
                    )
                ),
            }
        )

        return (
            MedicalDocumentExtraction
            .model_validate(payload)
        )
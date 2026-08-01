from __future__ import annotations

import re
from collections.abc import Callable
from typing import Any, TypeVar

from app.schemas.medical_extraction import (
    ExtractionStatus,
    MedicalDocumentExtraction,
)

ExtractionItem = TypeVar("ExtractionItem")


class MedicalExtractionMergeService:
    """
    Merge deterministic and LLM extraction results.

    Deterministic facts are placed first and win when both extraction
    paths produce the same normalized fact. Final evidence validation,
    deduplication, status calculation, and confidence aggregation are
    handled by MedicalExtractionHardeningService at the orchestration
    boundary after this merge completes.
    """

    @staticmethod
    def _normalize(
        value: str | None,
    ) -> str:
        if not value:
            return ""

        normalized = value.casefold()
        normalized = re.sub(
            r"[^a-z0-9]+",
            " ",
            normalized,
        )
        return " ".join(
            normalized.split()
        )

    @classmethod
    def _merge_unique(
        cls,
        primary_items: list[ExtractionItem],
        secondary_items: list[ExtractionItem],
        key_builder: Callable[
            [ExtractionItem],
            Any,
        ],
    ) -> list[ExtractionItem]:
        merged: list[ExtractionItem] = []
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
            cls._normalize(item.test_name),
            cls._normalize(item.raw_value),
            cls._normalize(item.unit),
        )

    @classmethod
    def _medication_key(
        cls,
        item,
    ) -> tuple[str, str]:
        return (
            cls._normalize(item.name),
            cls._normalize(item.dose),
        )

    @classmethod
    def _provider_key(
        cls,
        item,
    ) -> tuple[str, str, str]:
        return (
            cls._normalize(item.name),
            cls._normalize(item.role),
            cls._normalize(item.organization),
        )

    @classmethod
    def _diagnosis_key(
        cls,
        item,
    ) -> tuple[str, str]:
        return (
            cls._normalize(item.name),
            cls._normalize(item.code),
        )

    @classmethod
    def _procedure_key(
        cls,
        item,
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
        item,
    ) -> str:
        return cls._normalize(
            item.instruction
        )

    @staticmethod
    def _warning_key(
        warning,
    ) -> tuple[str, str]:
        return warning.code, warning.message

    @classmethod
    def merge(
        cls,
        deterministic: MedicalDocumentExtraction,
        llm: MedicalDocumentExtraction,
    ) -> MedicalDocumentExtraction:
        if deterministic.document_id != llm.document_id:
            raise ValueError(
                "Extraction document IDs do not match."
            )

        patient_payload = llm.patient.model_dump(
            mode="python"
        )

        for field_name in (
            "name",
            "date_of_birth",
            "medical_record_number",
        ):
            deterministic_value = getattr(
                deterministic.patient,
                field_name,
            )

            if deterministic_value is not None:
                patient_payload[field_name] = (
                    deterministic_value.model_dump(
                        mode="python"
                    )
                )

        providers = cls._merge_unique(
            deterministic.providers,
            llm.providers,
            cls._provider_key,
        )
        diagnoses = cls._merge_unique(
            deterministic.diagnoses,
            llm.diagnoses,
            cls._diagnosis_key,
        )
        medications = cls._merge_unique(
            deterministic.medications,
            llm.medications,
            cls._medication_key,
        )
        lab_results = cls._merge_unique(
            deterministic.lab_results,
            llm.lab_results,
            cls._lab_key,
        )
        procedures = cls._merge_unique(
            deterministic.procedures,
            llm.procedures,
            cls._procedure_key,
        )
        follow_up_instructions = (
            cls._merge_unique(
                deterministic.follow_up_instructions,
                llm.follow_up_instructions,
                cls._follow_up_key,
            )
        )
        warnings = cls._merge_unique(
            deterministic.warnings,
            llm.warnings,
            cls._warning_key,
        )

        payload = llm.model_dump(
            mode="python"
        )
        payload.update(
            {
                "document_id": deterministic.document_id,
                "document_type": deterministic.document_type,
                "status": ExtractionStatus.PARTIAL,
                "patient": patient_payload,
                "document_date": (
                    deterministic.document_date
                    if deterministic.document_date
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
                # Recalculated after final evidence validation.
                "extraction_confidence": 0.0,
            }
        )

        return (
            MedicalDocumentExtraction
            .model_validate(payload)
        )
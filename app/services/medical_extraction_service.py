import json
import logging
import re
from datetime import date, datetime
from time import perf_counter
from typing import Any, Iterator

from pydantic import BaseModel, ValidationError
from sqlalchemy import select

from app.core.config import settings
from app.db.models import Document, DocumentChunk
from app.db.session import SessionLocal
from app.schemas.medical_extraction import (
    DiagnosisInformation,
    DiagnosisStatus,
    ExtractionMethod,
    ExtractionStatus,
    ExtractionWarning,
    FollowUpInstruction,
    LabResultFlag,
    LabResultInformation,
    MedicalDocumentExtraction,
    MedicalDocumentType,
    MedicationInformation,
    MedicationStatus,
    PatientInformation,
    ProcedureInformation,
    ProviderInformation,
    SourceEvidence,
    SourcedDateValue,
    SourcedTextValue,
)
from app.schemas.medical_extraction_candidate import (
    CandidateDiagnosisInformation,
    CandidateFollowUpInstruction,
    CandidateLabResultInformation,
    CandidateMedicationInformation,
    CandidateProcedureInformation,
    CandidateProviderInformation,
    MedicalExtractionCandidate,
)
from app.services.deterministic_medical_extraction_service import (
    DeterministicMedicalExtractionService,
)
from app.services.llm_service import LLMService
from app.services.medical_extraction_merge_service import (
    MedicalExtractionMergeService,
)
from app.services.medical_extraction_prompt_service import (
    MedicalExtractionPromptService,
)


logger = logging.getLogger(__name__)


class MedicalExtractionError(RuntimeError):
    pass


class MedicalExtractionNotFoundError(MedicalExtractionError):
    pass


class MedicalExtractionContentTooLargeError(
    MedicalExtractionError
):
    pass


class MedicalExtractionValidationError(
    MedicalExtractionError
):
    pass


class MedicalExtractionService:
    """
    Build a strict medical extraction from deterministic facts and a
    lightweight LLM candidate response.

    The LLM never controls source metadata, confidence values, extraction
    methods, or document ownership. The server locates exact source text,
    constructs trusted evidence, validates the result, and then merges it
    with deterministic extraction.
    """

    MAX_DOCUMENT_CHARACTERS = (
        settings.extraction_max_context_characters
    )
    MAX_ATTEMPTS = 2
    MINIMUM_OVERLAP_CHARACTERS = 20
    SOURCE_WINDOW_LINES = 3

    DATE_FORMATS = (
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%m-%d-%Y",
        "%d/%m/%Y",
        "%B %d, %Y",
        "%b %d, %Y",
        "%B %d %Y",
        "%b %d %Y",
    )

    @staticmethod
    def _elapsed_ms(started_at: float) -> float:
        return round(
            (perf_counter() - started_at) * 1000,
            3,
        )

    @staticmethod
    def _normalize_document_type(
        value: str | None,
    ) -> MedicalDocumentType:
        try:
            return MedicalDocumentType(
                value or "unknown"
            )
        except ValueError:
            return MedicalDocumentType.UNKNOWN

    @classmethod
    def _load_document_context(
        cls,
        document_id: str,
        user_id: str,
    ) -> tuple[
        dict[str, Any],
        list[dict[str, Any]],
    ]:
        statement = (
            select(
                Document.document_id.label(
                    "document_id"
                ),
                Document.original_filename.label(
                    "filename"
                ),
                Document.document_type.label(
                    "document_type"
                ),
                Document.source.label("source"),
                Document.file_size_bytes.label(
                    "file_size_bytes"
                ),
                DocumentChunk.chunk_id.label(
                    "chunk_id"
                ),
                DocumentChunk.page_number.label(
                    "page_number"
                ),
                DocumentChunk.chunk_index.label(
                    "chunk_index"
                ),
                DocumentChunk.text.label("text"),
            )
            .select_from(Document)
            .outerjoin(
                DocumentChunk,
                DocumentChunk.document_id
                == Document.document_id,
            )
            .where(
                Document.document_id == document_id,
                Document.user_id == user_id,
            )
            .order_by(
                DocumentChunk.chunk_index.asc(),
                DocumentChunk.id.asc(),
            )
        )

        db = SessionLocal()

        try:
            rows = db.execute(statement).all()
        finally:
            db.close()

        if not rows:
            raise MedicalExtractionNotFoundError(
                "Document not found."
            )

        first_row = rows[0]

        document = {
            "document_id": str(
                first_row.document_id
            ),
            "filename": first_row.filename,
            "document_type": (
                first_row.document_type
            ),
            "source": first_row.source,
            "file_size_bytes": (
                first_row.file_size_bytes
            ),
        }

        chunks = [
            {
                "chunk_id": str(row.chunk_id),
                "document_id": str(
                    row.document_id
                ),
                "page_number": row.page_number,
                "chunk_index": int(
                    row.chunk_index
                ),
                "text": str(
                    row.text or ""
                ).strip(),
            }
            for row in rows
            if (
                row.chunk_id is not None
                and str(row.text or "").strip()
            )
        ]

        if not chunks:
            raise MedicalExtractionError(
                "The document has no readable indexed chunks."
            )

        return document, chunks

    @staticmethod
    def _extract_json_object(
        response_text: str,
    ) -> dict[str, Any]:
        cleaned = (response_text or "").strip()

        if not cleaned:
            raise MedicalExtractionValidationError(
                "The model returned an empty response."
            )

        if cleaned.startswith("```"):
            cleaned = re.sub(
                r"^```(?:json)?\s*",
                "",
                cleaned,
                flags=re.IGNORECASE,
            )
            cleaned = re.sub(
                r"\s*```$",
                "",
                cleaned,
            ).strip()

        try:
            payload = json.loads(cleaned)
        except json.JSONDecodeError:
            object_start = cleaned.find("{")
            object_end = cleaned.rfind("}")

            if (
                object_start == -1
                or object_end == -1
                or object_end <= object_start
            ):
                raise MedicalExtractionValidationError(
                    "The model response did not contain a JSON object."
                )

            try:
                payload = json.loads(
                    cleaned[
                        object_start:
                        object_end + 1
                    ]
                )
            except json.JSONDecodeError as exc:
                raise MedicalExtractionValidationError(
                    "The model returned malformed JSON."
                ) from exc

        if not isinstance(payload, dict):
            raise MedicalExtractionValidationError(
                "The extraction response must be a JSON object."
            )

        return payload

    @classmethod
    def _validate_document_size(
        cls,
        chunks: list[dict[str, Any]],
    ) -> None:
        character_count = sum(
            len(str(chunk.get("text") or ""))
            for chunk in chunks
        )

        if character_count > cls.MAX_DOCUMENT_CHARACTERS:
            raise MedicalExtractionContentTooLargeError(
                "The document is too large for the current "
                "extraction pipeline."
            )

    @staticmethod
    def _normalize_overlap_text(value: str) -> str:
        return (
            value.replace("\r\n", "\n")
            .replace("\r", "\n")
            .strip()
        )

    @classmethod
    def _remove_leading_overlap(
        cls,
        previous_text: str,
        incoming_text: str,
    ) -> str:
        previous = cls._normalize_overlap_text(
            previous_text
        )
        incoming = cls._normalize_overlap_text(
            incoming_text
        )

        if not previous:
            return incoming

        if not incoming:
            return ""

        if incoming in previous:
            return ""

        if previous in incoming:
            return incoming

        maximum_overlap = min(
            len(previous),
            len(incoming),
        )

        for overlap_size in range(
            maximum_overlap,
            cls.MINIMUM_OVERLAP_CHARACTERS - 1,
            -1,
        ):
            if (
                previous[-overlap_size:]
                == incoming[:overlap_size]
            ):
                return incoming[
                    overlap_size:
                ].lstrip()

        return incoming

    @classmethod
    def _prepare_prompt_chunks(
        cls,
        chunks: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        prompt_chunks: list[dict[str, Any]] = []
        seen_texts: set[str] = set()
        previous_text_by_page: dict[
            int | None,
            str,
        ] = {}

        for chunk in chunks:
            original_text = cls._normalize_overlap_text(
                str(chunk.get("text") or "")
            )

            if not original_text:
                continue

            normalized_exact = cls._normalize_match_text(
                original_text
            )

            if normalized_exact in seen_texts:
                continue

            seen_texts.add(normalized_exact)
            page_number = chunk.get("page_number")
            previous_text = previous_text_by_page.get(
                page_number,
                "",
            )

            compact_text = cls._remove_leading_overlap(
                previous_text=previous_text,
                incoming_text=original_text,
            )

            previous_text_by_page[
                page_number
            ] = original_text

            if not compact_text:
                continue

            prompt_chunk = dict(chunk)
            prompt_chunk["text"] = compact_text
            prompt_chunks.append(prompt_chunk)

        if not prompt_chunks:
            raise MedicalExtractionError(
                "The document has no unique text available for extraction."
            )

        return prompt_chunks

    @staticmethod
    def _build_chunk_map(
        chunks: list[dict[str, Any]],
    ) -> dict[str, dict[str, Any]]:
        chunk_map: dict[
            str,
            dict[str, Any],
        ] = {}

        for chunk in chunks:
            chunk_id = str(chunk["chunk_id"])

            if chunk_id in chunk_map:
                raise MedicalExtractionError(
                    "Duplicate chunk identifiers were found."
                )

            chunk_map[chunk_id] = chunk

        return chunk_map

    @staticmethod
    def _normalize_evidence_text(
        value: str,
    ) -> str:
        return " ".join(value.split()).casefold()

    @staticmethod
    def _normalize_match_text(
        value: str,
    ) -> str:
        normalized = " ".join(
            value.casefold().split()
        )
        return normalized.strip(" \t\n\r.,;:")

    @classmethod
    def _iter_source_evidence(
        cls,
        value: Any,
    ) -> Iterator[SourceEvidence]:
        if isinstance(value, SourceEvidence):
            yield value
            return

        if isinstance(value, BaseModel):
            for field_name in type(value).model_fields:
                yield from cls._iter_source_evidence(
                    getattr(value, field_name)
                )
            return

        if isinstance(value, list):
            for item in value:
                yield from cls._iter_source_evidence(
                    item
                )
            return

        if isinstance(value, dict):
            for item in value.values():
                yield from cls._iter_source_evidence(
                    item
                )

    @classmethod
    def _validate_evidence(
        cls,
        extraction: MedicalDocumentExtraction,
        chunks: list[dict[str, Any]],
        chunk_map: (
            dict[str, dict[str, Any]] | None
        ) = None,
        normalized_chunk_map: (
            dict[str, str] | None
        ) = None,
    ) -> None:
        resolved_chunk_map = (
            chunk_map
            if chunk_map is not None
            else cls._build_chunk_map(chunks)
        )

        resolved_normalized_map = (
            normalized_chunk_map
            if normalized_chunk_map is not None
            else {
                chunk_id: cls._normalize_evidence_text(
                    str(chunk.get("text") or "")
                )
                for chunk_id, chunk
                in resolved_chunk_map.items()
            }
        )

        for source in cls._iter_source_evidence(
            extraction
        ):
            chunk = resolved_chunk_map.get(
                source.chunk_id
            )

            if chunk is None:
                raise MedicalExtractionValidationError(
                    "An extracted source references an unknown chunk."
                )

            if source.chunk_index != chunk["chunk_index"]:
                raise MedicalExtractionValidationError(
                    "An extracted source has an invalid chunk index."
                )

            if (
                source.page_number
                != chunk.get("page_number")
            ):
                raise MedicalExtractionValidationError(
                    "An extracted source has an invalid page number."
                )

            normalized_quote = cls._normalize_evidence_text(
                source.quoted_text
            )
            normalized_chunk = (
                resolved_normalized_map[
                    source.chunk_id
                ]
            )

            if (
                not normalized_quote
                or normalized_quote
                not in normalized_chunk
            ):
                raise MedicalExtractionValidationError(
                    "An extracted source quote was not found in its "
                    "referenced chunk."
                )

    @classmethod
    def _candidate_anchors(
        cls,
        *values: str | None,
    ) -> list[str]:
        anchors: list[str] = []
        seen: set[str] = set()

        for value in values:
            if value is None:
                continue

            normalized = cls._normalize_match_text(
                value
            )

            if not normalized or normalized in seen:
                continue

            seen.add(normalized)
            anchors.append(normalized)

        return anchors

    @classmethod
    def _find_source(
        cls,
        *,
        document: dict[str, Any],
        chunks: list[dict[str, Any]],
        anchors: list[str],
        fact_name: str,
    ) -> SourceEvidence:
        if not anchors:
            raise MedicalExtractionValidationError(
                f"The candidate {fact_name} has no searchable value."
            )

        best_match: tuple[
            int,
            dict[str, Any],
            str,
        ] | None = None

        for chunk in chunks:
            lines = [
                line.strip()
                for line in str(
                    chunk.get("text") or ""
                ).splitlines()
                if line.strip()
            ]

            if not lines:
                continue

            maximum_window = min(
                cls.SOURCE_WINDOW_LINES,
                len(lines),
            )

            for window_size in range(
                1,
                maximum_window + 1,
            ):
                for start_index in range(
                    0,
                    len(lines) - window_size + 1,
                ):
                    quote = "\n".join(
                        lines[
                            start_index:
                            start_index + window_size
                        ]
                    )
                    normalized_quote = (
                        cls._normalize_match_text(
                            quote
                        )
                    )

                    if not all(
                        anchor in normalized_quote
                        for anchor in anchors
                    ):
                        continue

                    match = (
                        len(quote),
                        chunk,
                        quote,
                    )

                    if (
                        best_match is None
                        or match[0] < best_match[0]
                    ):
                        best_match = match

        if best_match is None:
            raise MedicalExtractionValidationError(
                f"The candidate {fact_name} could not be verified "
                "against the document text."
            )

        _, chunk, quote = best_match

        return SourceEvidence(
            document_id=str(
                document["document_id"]
            ),
            chunk_id=str(chunk["chunk_id"]),
            source_filename=document.get(
                "filename"
            ),
            page_number=chunk.get(
                "page_number"
            ),
            chunk_index=int(
                chunk["chunk_index"]
            ),
            quoted_text=quote,
        )

    @classmethod
    def _parse_date(
        cls,
        raw_value: str,
    ) -> date | None:
        cleaned = raw_value.strip().rstrip(
            ".,;"
        )

        for date_format in cls.DATE_FORMATS:
            try:
                return datetime.strptime(
                    cleaned,
                    date_format,
                ).date()
            except ValueError:
                continue

        return None

    @staticmethod
    def _numeric_value(
        raw_value: str,
    ) -> float | None:
        cleaned = re.sub(
            r"^[<>]=?\s*",
            "",
            raw_value.strip(),
        )

        try:
            return float(cleaned)
        except ValueError:
            return None

    @classmethod
    def _sourced_text_value(
        cls,
        *,
        value: str,
        document: dict[str, Any],
        chunks: list[dict[str, Any]],
        fact_name: str,
        confidence: float,
    ) -> SourcedTextValue:
        source = cls._find_source(
            document=document,
            chunks=chunks,
            anchors=cls._candidate_anchors(
                value
            ),
            fact_name=fact_name,
        )

        return SourcedTextValue(
            value=value,
            confidence=confidence,
            extraction_method=(
                ExtractionMethod.LLM
            ),
            sources=[source],
        )

    @classmethod
    def _sourced_date_value(
        cls,
        *,
        raw_value: str,
        document: dict[str, Any],
        chunks: list[dict[str, Any]],
        fact_name: str,
        confidence: float,
    ) -> SourcedDateValue:
        source = cls._find_source(
            document=document,
            chunks=chunks,
            anchors=cls._candidate_anchors(
                raw_value
            ),
            fact_name=fact_name,
        )

        return SourcedDateValue(
            raw_value=raw_value,
            normalized_value=cls._parse_date(
                raw_value
            ),
            confidence=confidence,
            extraction_method=(
                ExtractionMethod.LLM
            ),
            sources=[source],
        )

    @classmethod
    def _diagnosis_status(
        cls,
        status: DiagnosisStatus,
        quote: str,
    ) -> DiagnosisStatus:
        if status == DiagnosisStatus.UNKNOWN:
            return status

        normalized = cls._normalize_match_text(
            quote
        )

        support_terms = {
            DiagnosisStatus.ACTIVE: (
                "active",
                "current",
            ),
            DiagnosisStatus.RESOLVED: (
                "resolved",
            ),
            DiagnosisStatus.HISTORICAL: (
                "historical",
                "history of",
                "past medical history",
            ),
            DiagnosisStatus.RULED_OUT: (
                "ruled out",
                "rule out",
            ),
        }

        if any(
            term in normalized
            for term in support_terms.get(
                status,
                (),
            )
        ):
            return status

        return DiagnosisStatus.UNKNOWN

    @classmethod
    def _medication_status(
        cls,
        status: MedicationStatus,
        quote: str,
    ) -> MedicationStatus:
        if status == MedicationStatus.UNKNOWN:
            return status

        normalized = cls._normalize_match_text(
            quote
        )

        support_terms = {
            MedicationStatus.CURRENT: (
                "current",
                "continue",
                "continued",
            ),
            MedicationStatus.HISTORICAL: (
                "historical",
                "previously",
                "past medication",
            ),
            MedicationStatus.DISCONTINUED: (
                "discontinued",
                "stopped",
                "stop",
            ),
            MedicationStatus.AS_NEEDED: (
                "as needed",
                "prn",
            ),
        }

        if any(
            term in normalized
            for term in support_terms.get(
                status,
                (),
            )
        ):
            return status

        return MedicationStatus.UNKNOWN

    @classmethod
    def _lab_flag(
        cls,
        flag: LabResultFlag,
        quote: str,
        raw_value: str,
    ) -> LabResultFlag:
        if flag == LabResultFlag.UNKNOWN:
            return flag

        normalized_quote = (
            cls._normalize_match_text(quote)
        )
        normalized_value = (
            cls._normalize_match_text(raw_value)
        )

        if (
            flag == LabResultFlag.POSITIVE
            and normalized_value == "positive"
        ):
            return flag

        if (
            flag == LabResultFlag.NEGATIVE
            and normalized_value == "negative"
        ):
            return flag

        if flag.value in normalized_quote:
            return flag

        if (
            flag == LabResultFlag.HIGH
            and re.search(
                r"(?:^|\s)h(?:\s|$)",
                normalized_quote,
            )
        ):
            return flag

        if (
            flag == LabResultFlag.LOW
            and re.search(
                r"(?:^|\s)l(?:\s|$)",
                normalized_quote,
            )
        ):
            return flag

        return LabResultFlag.UNKNOWN

    @classmethod
    def _convert_provider(
        cls,
        candidate: CandidateProviderInformation,
        document: dict[str, Any],
        chunks: list[dict[str, Any]],
    ) -> ProviderInformation:
        source = cls._find_source(
            document=document,
            chunks=chunks,
            anchors=cls._candidate_anchors(
                candidate.name,
                candidate.role,
                candidate.organization,
            ),
            fact_name=(
                f"provider '{candidate.name}'"
            ),
        )

        return ProviderInformation(
            name=candidate.name,
            role=candidate.role,
            organization=candidate.organization,
            confidence=0.88,
            extraction_method=ExtractionMethod.LLM,
            sources=[source],
        )

    @classmethod
    def _convert_diagnosis(
        cls,
        candidate: CandidateDiagnosisInformation,
        document: dict[str, Any],
        chunks: list[dict[str, Any]],
    ) -> DiagnosisInformation:
        source = cls._find_source(
            document=document,
            chunks=chunks,
            anchors=cls._candidate_anchors(
                candidate.name,
                candidate.code,
                candidate.code_system,
            ),
            fact_name=(
                f"diagnosis '{candidate.name}'"
            ),
        )

        return DiagnosisInformation(
            name=candidate.name,
            code=candidate.code,
            code_system=candidate.code_system,
            status=cls._diagnosis_status(
                candidate.status,
                source.quoted_text,
            ),
            confidence=0.86,
            extraction_method=ExtractionMethod.LLM,
            sources=[source],
        )

    @classmethod
    def _convert_medication(
        cls,
        candidate: CandidateMedicationInformation,
        document: dict[str, Any],
        chunks: list[dict[str, Any]],
    ) -> MedicationInformation:
        source = cls._find_source(
            document=document,
            chunks=chunks,
            anchors=cls._candidate_anchors(
                candidate.name,
                candidate.dose,
                candidate.route,
                candidate.frequency,
                candidate.duration,
                candidate.instructions,
            ),
            fact_name=(
                f"medication '{candidate.name}'"
            ),
        )

        return MedicationInformation(
            name=candidate.name,
            dose=candidate.dose,
            route=candidate.route,
            frequency=candidate.frequency,
            duration=candidate.duration,
            instructions=candidate.instructions,
            status=cls._medication_status(
                candidate.status,
                source.quoted_text,
            ),
            confidence=0.88,
            extraction_method=ExtractionMethod.LLM,
            sources=[source],
        )

    @classmethod
    def _convert_lab_result(
        cls,
        candidate: CandidateLabResultInformation,
        document: dict[str, Any],
        chunks: list[dict[str, Any]],
    ) -> LabResultInformation:
        source = cls._find_source(
            document=document,
            chunks=chunks,
            anchors=cls._candidate_anchors(
                candidate.test_name,
                candidate.raw_value,
                candidate.unit,
                candidate.reference_range,
            ),
            fact_name=(
                "lab result "
                f"'{candidate.test_name}'"
            ),
        )

        collected_at = None

        if candidate.collected_at is not None:
            collected_at = cls._sourced_date_value(
                raw_value=candidate.collected_at,
                document=document,
                chunks=chunks,
                fact_name=(
                    "lab collection date"
                ),
                confidence=0.86,
            )

        return LabResultInformation(
            test_name=candidate.test_name,
            raw_value=candidate.raw_value,
            numeric_value=cls._numeric_value(
                candidate.raw_value
            ),
            unit=candidate.unit,
            reference_range=(
                candidate.reference_range
            ),
            flag=cls._lab_flag(
                candidate.flag,
                source.quoted_text,
                candidate.raw_value,
            ),
            collected_at=collected_at,
            confidence=0.90,
            extraction_method=ExtractionMethod.LLM,
            sources=[source],
        )

    @classmethod
    def _convert_procedure(
        cls,
        candidate: CandidateProcedureInformation,
        document: dict[str, Any],
        chunks: list[dict[str, Any]],
    ) -> ProcedureInformation:
        source = cls._find_source(
            document=document,
            chunks=chunks,
            anchors=cls._candidate_anchors(
                candidate.name,
                candidate.result,
            ),
            fact_name=(
                f"procedure '{candidate.name}'"
            ),
        )

        procedure_date = None

        if candidate.procedure_date is not None:
            procedure_date = cls._sourced_date_value(
                raw_value=candidate.procedure_date,
                document=document,
                chunks=chunks,
                fact_name="procedure date",
                confidence=0.85,
            )

        return ProcedureInformation(
            name=candidate.name,
            procedure_date=procedure_date,
            result=candidate.result,
            confidence=0.86,
            extraction_method=ExtractionMethod.LLM,
            sources=[source],
        )

    @classmethod
    def _convert_follow_up(
        cls,
        candidate: CandidateFollowUpInstruction,
        document: dict[str, Any],
        chunks: list[dict[str, Any]],
    ) -> FollowUpInstruction:
        source = cls._find_source(
            document=document,
            chunks=chunks,
            anchors=cls._candidate_anchors(
                candidate.instruction,
                candidate.timeframe,
                candidate.specialty,
            ),
            fact_name="follow-up instruction",
        )

        return FollowUpInstruction(
            instruction=candidate.instruction,
            timeframe=candidate.timeframe,
            specialty=candidate.specialty,
            confidence=0.86,
            extraction_method=ExtractionMethod.LLM,
            sources=[source],
        )

    @classmethod
    def _candidate_to_extraction(
        cls,
        *,
        candidate: MedicalExtractionCandidate,
        document: dict[str, Any],
        chunks: list[dict[str, Any]],
    ) -> MedicalDocumentExtraction:
        confidence_values: list[float] = []

        patient_name = None
        if candidate.patient.name is not None:
            patient_name = cls._sourced_text_value(
                value=candidate.patient.name,
                document=document,
                chunks=chunks,
                fact_name="patient name",
                confidence=0.90,
            )
            confidence_values.append(
                patient_name.confidence
            )

        date_of_birth = None
        if candidate.patient.date_of_birth is not None:
            date_of_birth = cls._sourced_date_value(
                raw_value=(
                    candidate.patient.date_of_birth
                ),
                document=document,
                chunks=chunks,
                fact_name="patient date of birth",
                confidence=0.90,
            )
            confidence_values.append(
                date_of_birth.confidence
            )

        medical_record_number = None
        if (
            candidate.patient
            .medical_record_number
            is not None
        ):
            medical_record_number = (
                cls._sourced_text_value(
                    value=(
                        candidate.patient
                        .medical_record_number
                    ),
                    document=document,
                    chunks=chunks,
                    fact_name=(
                        "medical record number"
                    ),
                    confidence=0.90,
                )
            )
            confidence_values.append(
                medical_record_number.confidence
            )

        patient = PatientInformation(
            name=patient_name,
            date_of_birth=date_of_birth,
            medical_record_number=(
                medical_record_number
            ),
        )

        document_date = None
        if candidate.document_date is not None:
            document_date = cls._sourced_date_value(
                raw_value=candidate.document_date,
                document=document,
                chunks=chunks,
                fact_name="document date",
                confidence=0.88,
            )
            confidence_values.append(
                document_date.confidence
            )

        providers = [
            cls._convert_provider(
                provider,
                document,
                chunks,
            )
            for provider in candidate.providers
        ]

        diagnoses = [
            cls._convert_diagnosis(
                diagnosis,
                document,
                chunks,
            )
            for diagnosis in candidate.diagnoses
        ]

        medications = [
            cls._convert_medication(
                medication,
                document,
                chunks,
            )
            for medication in candidate.medications
        ]

        lab_results = [
            cls._convert_lab_result(
                lab_result,
                document,
                chunks,
            )
            for lab_result in candidate.lab_results
        ]

        procedures = [
            cls._convert_procedure(
                procedure,
                document,
                chunks,
            )
            for procedure in candidate.procedures
        ]

        follow_up_instructions = [
            cls._convert_follow_up(
                instruction,
                document,
                chunks,
            )
            for instruction
            in candidate.follow_up_instructions
        ]

        for collection in (
            providers,
            diagnoses,
            medications,
            lab_results,
            procedures,
            follow_up_instructions,
        ):
            confidence_values.extend(
                item.confidence
                for item in collection
            )

        has_facts = bool(confidence_values)
        extraction_confidence = (
            round(
                sum(confidence_values)
                / len(confidence_values),
                3,
            )
            if confidence_values
            else 0.0
        )

        return MedicalDocumentExtraction(
            document_id=str(
                document["document_id"]
            ),
            document_type=(
                cls._normalize_document_type(
                    document.get(
                        "document_type"
                    )
                )
            ),
            status=(
                ExtractionStatus.COMPLETED
                if has_facts
                else ExtractionStatus.PARTIAL
            ),
            patient=patient,
            document_date=document_date,
            providers=providers,
            diagnoses=diagnoses,
            medications=medications,
            lab_results=lab_results,
            procedures=procedures,
            follow_up_instructions=(
                follow_up_instructions
            ),
            extraction_confidence=(
                extraction_confidence
            ),
        )

    @classmethod
    def _validate_candidate_output(
        cls,
        *,
        response_text: str,
        document: dict[str, Any],
        chunks: list[dict[str, Any]],
        chunk_map: dict[str, dict[str, Any]],
        normalized_chunk_map: dict[str, str],
    ) -> MedicalDocumentExtraction:
        payload = cls._extract_json_object(
            response_text
        )

        try:
            candidate = (
                MedicalExtractionCandidate
                .model_validate(payload)
            )
        except ValidationError as exc:
            raise MedicalExtractionValidationError(
                str(exc)
            ) from exc

        extraction = cls._candidate_to_extraction(
            candidate=candidate,
            document=document,
            chunks=chunks,
        )

        cls._validate_evidence(
            extraction=extraction,
            chunks=chunks,
            chunk_map=chunk_map,
            normalized_chunk_map=(
                normalized_chunk_map
            ),
        )

        return extraction

    @staticmethod
    def _has_extracted_facts(
        extraction: MedicalDocumentExtraction,
    ) -> bool:
        return any(
            (
                extraction.patient.name is not None,
                extraction.patient.date_of_birth
                is not None,
                extraction.patient
                .medical_record_number
                is not None,
                extraction.document_date is not None,
                bool(extraction.providers),
                bool(extraction.diagnoses),
                bool(extraction.medications),
                bool(extraction.lab_results),
                bool(extraction.procedures),
                bool(
                    extraction
                    .follow_up_instructions
                ),
            )
        )

    @staticmethod
    def _add_warning(
        extraction: MedicalDocumentExtraction,
        *,
        code: str,
        message: str,
    ) -> MedicalDocumentExtraction:
        warnings = list(extraction.warnings)

        if not any(
            warning.code == code
            for warning in warnings
        ):
            warnings.append(
                ExtractionWarning(
                    code=code,
                    message=message,
                )
            )

        return extraction.model_copy(
            update={
                "status": ExtractionStatus.PARTIAL,
                "warnings": warnings,
            }
        )

    @classmethod
    def _deterministic_fallback(
        cls,
        extraction: MedicalDocumentExtraction,
        *,
        code: str,
        message: str,
    ) -> MedicalDocumentExtraction | None:
        if (
            not settings
            .extraction_allow_deterministic_fallback
            or not cls._has_extracted_facts(
                extraction
            )
        ):
            return None

        return cls._add_warning(
            extraction,
            code=code,
            message=message,
        )

    @classmethod
    def extract(
        cls,
        document_id: str,
        user_id: str,
    ) -> MedicalDocumentExtraction:
        total_started_at = perf_counter()
        timings: dict[str, Any] = {}

        cleaned_document_id = document_id.strip()
        cleaned_user_id = user_id.strip()

        if not cleaned_document_id:
            raise ValueError(
                "document_id is required."
            )

        if not cleaned_user_id:
            raise ValueError(
                "user_id is required."
            )

        stage_started_at = perf_counter()
        document, chunks = cls._load_document_context(
            document_id=cleaned_document_id,
            user_id=cleaned_user_id,
        )
        timings["context_load_ms"] = (
            cls._elapsed_ms(stage_started_at)
        )

        stage_started_at = perf_counter()
        prompt_chunks = cls._prepare_prompt_chunks(
            chunks
        )
        cls._validate_document_size(prompt_chunks)

        chunk_map = cls._build_chunk_map(chunks)
        normalized_chunk_map = {
            chunk_id: cls._normalize_evidence_text(
                str(chunk.get("text") or "")
            )
            for chunk_id, chunk
            in chunk_map.items()
        }

        timings["context_prepare_ms"] = (
            cls._elapsed_ms(stage_started_at)
        )
        timings["raw_chunk_count"] = len(chunks)
        timings["prompt_chunk_count"] = len(
            prompt_chunks
        )
        timings["raw_context_characters"] = sum(
            len(chunk["text"])
            for chunk in chunks
        )
        timings[
            "prompt_context_characters"
        ] = sum(
            len(chunk["text"])
            for chunk in prompt_chunks
        )

        stage_started_at = perf_counter()
        deterministic_extraction = (
            DeterministicMedicalExtractionService
            .extract(
                document=document,
                chunks=chunks,
            )
        )
        cls._validate_evidence(
            extraction=deterministic_extraction,
            chunks=chunks,
            chunk_map=chunk_map,
            normalized_chunk_map=(
                normalized_chunk_map
            ),
        )
        timings[
            "deterministic_extraction_ms"
        ] = cls._elapsed_ms(stage_started_at)

        stage_started_at = perf_counter()
        extraction_prompt = (
            MedicalExtractionPromptService
            .build_extraction_prompt(
                document=document,
                chunks=prompt_chunks,
                deterministic_extraction=(
                    deterministic_extraction
                ),
            )
        )
        timings["prompt_build_ms"] = (
            cls._elapsed_ms(stage_started_at)
        )
        timings["prompt_characters"] = len(
            extraction_prompt
        )

        previous_output = ""
        previous_error = ""

        maximum_attempts = (
            cls.MAX_ATTEMPTS
            if settings.extraction_enable_repair
            else 1
        )

        for attempt_number in range(
            1,
            maximum_attempts + 1,
        ):
            if attempt_number == 1:
                prompt = extraction_prompt
            else:
                prompt = (
                    MedicalExtractionPromptService
                    .build_repair_prompt(
                        original_prompt=(
                            extraction_prompt
                        ),
                        invalid_output=(
                            previous_output
                        ),
                        validation_error=(
                            previous_error
                        ),
                    )
                )

            timings[
                f"attempt_{attempt_number}_prompt_characters"
            ] = len(prompt)

            stage_started_at = perf_counter()

            try:
                response_text = (
                    LLMService.generate_response(
                        prompt=prompt,
                        system_prompt=(
                            MedicalExtractionPromptService
                            .SYSTEM_PROMPT
                        ),
                        timeout_seconds=(
                            settings
                            .extraction_llm_timeout_seconds
                        ),
                        json_mode=True,
                        temperature=0.0,
                        max_output_tokens=(
                            settings
                            .extraction_llm_max_output_tokens
                        ),
                        context_window=(
                            settings
                            .extraction_llm_context_window
                        ),
                        keep_alive=(
                            settings
                            .extraction_llm_keep_alive
                        ),
                    )
                )
            except Exception as exc:
                timings[
                    f"attempt_{attempt_number}_llm_ms"
                ] = cls._elapsed_ms(
                    stage_started_at
                )
                timings["total_ms"] = (
                    cls._elapsed_ms(
                        total_started_at
                    )
                )

                if attempt_number == 1:
                    fallback = (
                        cls._deterministic_fallback(
                            deterministic_extraction,
                            code=(
                                "contextual_extraction_unavailable"
                            ),
                            message=(
                                "Contextual extraction was unavailable; "
                                "only deterministic facts were returned."
                            ),
                        )
                    )

                    if settings.extraction_log_timings:
                        logger.warning(
                            "medical_extraction_llm_failed "
                            "document_id=%s timings=%s error=%s",
                            cleaned_document_id,
                            timings,
                            str(exc),
                        )

                    if fallback is not None:
                        return fallback

                    raise MedicalExtractionError(
                        "The extraction model could not be reached."
                    ) from exc

                if settings.extraction_log_timings:
                    logger.warning(
                        "medical_extraction_repair_failed "
                        "document_id=%s timings=%s error=%s",
                        cleaned_document_id,
                        timings,
                        str(exc),
                    )

                raise MedicalExtractionValidationError(
                    "The candidate extraction repair could not be completed."
                ) from exc

            timings[
                f"attempt_{attempt_number}_llm_ms"
            ] = cls._elapsed_ms(
                stage_started_at
            )
            timings[
                f"attempt_{attempt_number}_response_characters"
            ] = len(response_text)

            stage_started_at = perf_counter()

            try:
                llm_extraction = (
                    cls._validate_candidate_output(
                        response_text=response_text,
                        document=document,
                        chunks=chunks,
                        chunk_map=chunk_map,
                        normalized_chunk_map=(
                            normalized_chunk_map
                        ),
                    )
                )

                merged_extraction = (
                    MedicalExtractionMergeService
                    .merge(
                        deterministic=(
                            deterministic_extraction
                        ),
                        llm=llm_extraction,
                    )
                )

                cls._validate_evidence(
                    extraction=merged_extraction,
                    chunks=chunks,
                    chunk_map=chunk_map,
                    normalized_chunk_map=(
                        normalized_chunk_map
                    ),
                )

                timings[
                    f"attempt_{attempt_number}_validation_ms"
                ] = cls._elapsed_ms(
                    stage_started_at
                )
                timings["total_ms"] = (
                    cls._elapsed_ms(
                        total_started_at
                    )
                )

                if settings.extraction_log_timings:
                    logger.info(
                        "medical_extraction_completed "
                        "document_id=%s timings=%s",
                        cleaned_document_id,
                        timings,
                    )

                return merged_extraction

            except (
                MedicalExtractionValidationError,
                ValidationError,
                ValueError,
            ) as exc:
                timings[
                    f"attempt_{attempt_number}_validation_ms"
                ] = cls._elapsed_ms(
                    stage_started_at
                )
                previous_output = response_text
                previous_error = str(exc)

                if settings.extraction_log_timings:
                    logger.warning(
                        "medical_extraction_validation_failed "
                        "document_id=%s attempt=%s error=%s",
                        cleaned_document_id,
                        attempt_number,
                        previous_error[:2000],
                    )

        timings["total_ms"] = cls._elapsed_ms(
            total_started_at
        )

        if settings.extraction_log_timings:
            logger.warning(
                "medical_extraction_exhausted_retries "
                "document_id=%s timings=%s last_error=%s",
                cleaned_document_id,
                timings,
                previous_error[:2000],
            )

        raise MedicalExtractionValidationError(
            "The document could not be converted into a valid "
            "structured extraction."
        )
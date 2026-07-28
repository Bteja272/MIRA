from typing import Any

from app.core.config import settings
from app.schemas.medical_extraction import (
    MedicalDocumentExtraction,
)


class MedicalExtractionPromptService:
    SYSTEM_PROMPT = """
You extract explicit facts from medical documents.

Return one JSON object only. Copy values exactly as written. Never infer,
diagnose, recommend treatment, convert units, or add information that is not
present in the supplied text. Use null or an empty list when a fact is absent.
""".strip()

    OUTPUT_CONTRACT = """
{
  "patient": {
    "name": string|null,
    "date_of_birth": string|null,
    "medical_record_number": string|null
  },
  "document_date": string|null,
  "providers": [
    {"name": string, "role": string|null, "organization": string|null}
  ],
  "diagnoses": [
    {
      "name": string,
      "code": string|null,
      "code_system": string|null,
      "status": "active"|"resolved"|"historical"|"ruled_out"|"unknown"
    }
  ],
  "medications": [
    {
      "name": string,
      "dose": string|null,
      "route": string|null,
      "frequency": string|null,
      "duration": string|null,
      "instructions": string|null,
      "status": "current"|"historical"|"discontinued"|"as_needed"|"unknown"
    }
  ],
  "lab_results": [
    {
      "test_name": string,
      "raw_value": string,
      "unit": string|null,
      "reference_range": string|null,
      "flag": "high"|"low"|"normal"|"abnormal"|"critical"|"positive"|"negative"|"unknown",
      "collected_at": string|null
    }
  ],
  "procedures": [
    {"name": string, "procedure_date": string|null, "result": string|null}
  ],
  "follow_up_instructions": [
    {"instruction": string, "timeframe": string|null, "specialty": string|null}
  ]
}
""".strip()

    @staticmethod
    def _format_chunk(
        chunk: dict[str, Any],
    ) -> str:
        page_number = chunk.get("page_number")
        page_display = (
            str(page_number)
            if page_number is not None
            else "unknown"
        )

        return (
            f'<chunk id="{chunk["chunk_id"]}" '
            f'page="{page_display}" '
            f'index="{chunk["chunk_index"]}">\n'
            f'{chunk["text"]}\n'
            "</chunk>"
        )

    @staticmethod
    def _clean_summary_value(
        value: str | None,
    ) -> str:
        return " ".join((value or "").split())

    @classmethod
    def _build_known_fact_summary(
        cls,
        extraction: MedicalDocumentExtraction | None,
    ) -> str:
        if extraction is None:
            return "none"

        facts: list[str] = []

        if extraction.patient.name is not None:
            facts.append(
                "patient.name="
                + cls._clean_summary_value(
                    extraction.patient.name.value
                )
            )

        if extraction.patient.date_of_birth is not None:
            facts.append(
                "patient.date_of_birth="
                + cls._clean_summary_value(
                    extraction.patient.date_of_birth.raw_value
                )
            )

        if (
            extraction.patient.medical_record_number
            is not None
        ):
            facts.append(
                "patient.medical_record_number="
                + cls._clean_summary_value(
                    extraction.patient
                    .medical_record_number
                    .value
                )
            )

        if extraction.document_date is not None:
            facts.append(
                "document_date="
                + cls._clean_summary_value(
                    extraction.document_date.raw_value
                )
            )

        for medication in extraction.medications:
            facts.append(
                "medication="
                + cls._clean_summary_value(
                    medication.name
                )
                + "|"
                + cls._clean_summary_value(
                    medication.dose
                )
            )

        for lab_result in extraction.lab_results:
            facts.append(
                "lab="
                + cls._clean_summary_value(
                    lab_result.test_name
                )
                + "|"
                + cls._clean_summary_value(
                    lab_result.raw_value
                )
                + "|"
                + cls._clean_summary_value(
                    lab_result.unit
                )
            )

        if not facts:
            return "none"

        return "\n".join(
            f"- {fact}"
            for fact in facts
        )[:2500]

    @classmethod
    def build_extraction_prompt(
        cls,
        document: dict[str, Any],
        chunks: list[dict[str, Any]],
        deterministic_extraction: (
            MedicalDocumentExtraction | None
        ) = None,
    ) -> str:
        formatted_chunks = "\n".join(
            cls._format_chunk(chunk)
            for chunk in chunks
        )

        known_facts = cls._build_known_fact_summary(
            deterministic_extraction
        )

        return f"""
Extract only explicit facts from the document context.

Document type: {document.get("document_type") or "unknown"}

Already extracted by deterministic code; do not repeat these exact facts:
{known_facts}

Return this lightweight JSON shape:
{cls.OUTPUT_CONTRACT}

Rules:
- Copy every returned string exactly from the document text.
- Omit unsupported facts; do not guess.
- Use "unknown" for a status or flag unless the document explicitly states it.
- Return no confidence values, evidence objects, metadata, warnings, or extra keys.
- The server will locate exact supporting text and create trusted evidence.

Document context:
{formatted_chunks}

Return one JSON object only.
""".strip()

    @staticmethod
    def _truncate_middle(
        value: str,
        maximum_characters: int,
    ) -> str:
        if len(value) <= maximum_characters:
            return value

        marker = "\n...[middle removed]...\n"
        remaining = maximum_characters - len(marker)

        if remaining <= 0:
            return value[:maximum_characters]

        head_size = remaining // 2
        tail_size = remaining - head_size

        return (
            value[:head_size]
            + marker
            + value[-tail_size:]
        )

    @classmethod
    def build_repair_prompt(
        cls,
        original_prompt: str,
        invalid_output: str,
        validation_error: str,
    ) -> str:
        total_budget = (
            settings
            .extraction_max_repair_prompt_characters
        )

        error_budget = min(
            1200,
            max(400, total_budget // 8),
        )

        output_budget = min(
            2500,
            max(1000, total_budget // 4),
        )

        original_budget = max(
            1800,
            total_budget
            - error_budget
            - output_budget,
        )

        compact_original = cls._truncate_middle(
            original_prompt,
            original_budget,
        )

        compact_output = cls._truncate_middle(
            invalid_output,
            output_budget,
        )

        compact_error = validation_error[
            :error_budget
        ]

        return f"""
The previous candidate JSON was invalid or contained unsupported facts.
Return one corrected JSON object matching the lightweight contract in the
original request. Remove any fact that is not copied exactly from the supplied
document. Do not add confidence values, sources, metadata, or explanations.

Validation error:
{compact_error}

Previous output:
{compact_output}

Original request:
{compact_original}
""".strip()
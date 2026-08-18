from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class GroundedResponseValidation:
    is_valid: bool
    issues: tuple[str, ...]
    unsupported_medical_values: tuple[str, ...]
    invalid_citation_numbers: tuple[int, ...]
    uncited_medical_values: tuple[str, ...]
    misattributed_medical_values: tuple[str, ...]


class ResponseValidationService:
    """
    Deterministic post-generation validation for document-grounded
    medical answers.

    Existing laboratory-interpretation sanitization is preserved.
    Grounded validation additionally checks:
    - source-label existence,
    - unsupported medical numeric claims,
    - missing citations for medical numeric claims, and
    - numeric claims cited only to sources that do not contain them.

    This layer does not invent or rewrite medical facts.
    """

    CITATION_PATTERN = re.compile(
        r"\[\s*Source\s+(\d+)\s*\]",
        re.IGNORECASE,
    )

    UNSUPPORTED_INTERPRETATION_PATTERNS = (
        re.compile(
            (
                r"\b(?:result|value|level|measurement)"
                r"\s+(?:is|was|appears|seems)"
                r"\s+(?:above|below|within|outside"
                r"(?:\s+of)?)"
                r"\s+(?:the\s+)?reference\s+range\b"
            ),
            re.IGNORECASE,
        ),
        re.compile(
            (
                r"\b(?:it|this)"
                r"\s+(?:is|was|appears|seems)"
                r"\s+(?:above|below|within|outside"
                r"(?:\s+of)?)"
                r"\s+(?:the\s+)?reference\s+range\b"
            ),
            re.IGNORECASE,
        ),
        re.compile(
            (
                r"\b(?:above|below|within|outside"
                r"(?:\s+of)?)"
                r"\s+(?:the\s+)?reference\s+range\b"
            ),
            re.IGNORECASE,
        ),
        re.compile(
            (
                r"\b(?:result|value|level|measurement)"
                r"\s+(?:is|was|appears|seems)"
                r"\s+(?:high|low|normal|abnormal)\b"
            ),
            re.IGNORECASE,
        ),
    )

    _VALUE_END = r"(?=\s|[.,;:)\]\}]|$)"

    MEDICAL_VALUE_PATTERNS = (
        re.compile(
            r"\b20\d{2}-\d{2}-\d{2}\b"
        ),
        re.compile(
            (
                r"\b[A-Z]\d{2}"
                r"(?:\.\d+)?\b"
            )
        ),
        re.compile(
            (
                r"\b\d{2,3}/\d{2,3}"
                r"\s*mmHg"
                + _VALUE_END
            ),
            re.IGNORECASE,
        ),
        re.compile(
            (
                r"\b\d+(?:\.\d+)?\s*"
                r"(?:"
                r"mg/dL|mg|mcg|g|"
                r"mmol/L|"
                r"mL/min/1\.73\s*m2|"
                r"mmHg|%|"
                r"days?|weeks?|months?"
                r")"
                + _VALUE_END
            ),
            re.IGNORECASE,
        ),
    )

    @staticmethod
    def _plain_text(
        value: str,
    ) -> str:
        return re.sub(
            r"[*_`]",
            "",
            value,
        )

    @staticmethod
    def _compact_text(
        value: str,
    ) -> str:
        return re.sub(
            r"\s+",
            "",
            (value or "").casefold(),
        )

    @classmethod
    def contains_unsupported_interpretation(
        cls,
        value: str,
    ) -> bool:
        plain_value = cls._plain_text(
            value
        )

        return any(
            pattern.search(
                plain_value
            )
            is not None
            for pattern
            in cls
            .UNSUPPORTED_INTERPRETATION_PATTERNS
        )

    @staticmethod
    def _split_sentences(
        line: str,
    ) -> list[str]:
        return re.split(
            r"(?<=[.!?])\s+",
            line,
        )

    @staticmethod
    def _collapse_blank_lines(
        lines: list[str],
    ) -> str:
        cleaned_lines: list[str] = []
        previous_was_blank = False

        for line in lines:
            stripped_line = line.rstrip()

            if not stripped_line:
                if previous_was_blank:
                    continue

                previous_was_blank = True
                cleaned_lines.append(
                    ""
                )
            else:
                previous_was_blank = False
                cleaned_lines.append(
                    stripped_line
                )

        return "\n".join(
            cleaned_lines
        ).strip()

    @classmethod
    def sanitize_document_answer(
        cls,
        answer: str,
    ) -> str:
        normalized_answer = (
            answer
            .replace("\r\n", "\n")
            .strip()
        )

        if not normalized_answer:
            return ""

        sanitized_lines: list[str] = []

        for line in normalized_answer.split(
            "\n"
        ):
            if not line.strip():
                sanitized_lines.append(
                    ""
                )
                continue

            sentences = (
                cls._split_sentences(
                    line
                )
            )

            retained_sentences = [
                sentence
                for sentence in sentences
                if (
                    sentence.strip()
                    and not cls
                    .contains_unsupported_interpretation(
                        sentence
                    )
                )
            ]

            if retained_sentences:
                sanitized_lines.append(
                    " ".join(
                        retained_sentences
                    )
                )

        sanitized_answer = (
            cls._collapse_blank_lines(
                sanitized_lines
            )
        )

        if sanitized_answer:
            return sanitized_answer

        return (
            "The generated response contained unsupported laboratory "
            "interpretation and was removed. Review the documented "
            "values, reference ranges, and flags in the cited sources."
        )

    @classmethod
    def _extract_medical_values(
        cls,
        value: str,
    ) -> list[str]:
        values: list[str] = []
        normalized_values: list[str] = []

        for pattern in cls.MEDICAL_VALUE_PATTERNS:
            for match in pattern.finditer(
                value or ""
            ):
                candidate = (
                    match.group(0)
                    .strip()
                )
                normalized = cls._compact_text(
                    candidate
                )

                if not normalized:
                    continue

                if normalized in normalized_values:
                    continue

                values.append(
                    candidate
                )
                normalized_values.append(
                    normalized
                )

        return values

    @staticmethod
    def _source_number(
        source: dict[str, Any],
        fallback: int,
    ) -> int:
        try:
            return int(
                source.get(
                    "source_number",
                    fallback,
                )
            )
        except (
            TypeError,
            ValueError,
        ):
            return fallback

    @staticmethod
    def _source_text(
        source: dict[str, Any],
    ) -> str:
        for key in (
            "text",
            "content",
            "page_content",
        ):
            value = source.get(
                key
            )

            if value:
                return str(
                    value
                )

        return ""

    @classmethod
    def _source_map(
        cls,
        sources: list[dict[str, Any]],
    ) -> dict[int, dict[str, Any]]:
        return {
            cls._source_number(
                source,
                index,
            ): source
            for index, source
            in enumerate(
                sources,
                start=1,
            )
        }

    @classmethod
    def _sentences_with_positions(
        cls,
        answer: str,
    ) -> list[str]:
        sentences: list[str] = []

        for line in (
            answer
            .replace("\r\n", "\n")
            .split("\n")
        ):
            stripped = line.strip()

            if not stripped:
                continue

            parts = cls._split_sentences(
                stripped
            )

            sentences.extend(
                part.strip()
                for part in parts
                if part.strip()
            )

        return sentences

    @classmethod
    def validate_grounded_answer(
        cls,
        *,
        answer: str,
        sources: list[dict[str, Any]],
    ) -> GroundedResponseValidation:
        issues: list[str] = []
        source_by_number = (
            cls._source_map(
                sources
            )
        )

        citation_numbers = [
            int(match.group(1))
            for match
            in cls.CITATION_PATTERN.finditer(
                answer or ""
            )
        ]

        invalid_citations = sorted(
            {
                number
                for number
                in citation_numbers
                if number
                not in source_by_number
            }
        )

        if invalid_citations:
            issues.append(
                "invalid_source_label"
            )

        # If document-grounded content was produced and sources exist,
        # at least one citation is required. This catches short answers
        # such as "7.2 %" that otherwise contain too little language for
        # broader sentence-level heuristics.
        if (
            sources
            and (answer or "").strip()
            and not citation_numbers
        ):
            issues.append(
                "missing_source_citation"
            )

        combined_source_text = "\n".join(
            cls._source_text(
                source
            )
            for source in sources
        )
        normalized_all_sources = (
            cls._compact_text(
                combined_source_text
            )
        )

        unsupported_values: list[str] = []
        uncited_values: list[str] = []
        misattributed_values: list[str] = []

        for medical_value in (
            cls._extract_medical_values(
                answer
            )
        ):
            normalized_value = (
                cls._compact_text(
                    medical_value
                )
            )

            if (
                normalized_value
                not in normalized_all_sources
            ):
                unsupported_values.append(
                    medical_value
                )

        for sentence in (
            cls._sentences_with_positions(
                answer
            )
        ):
            sentence_values = (
                cls._extract_medical_values(
                    sentence
                )
            )

            if not sentence_values:
                continue

            sentence_citations = [
                int(match.group(1))
                for match
                in cls.CITATION_PATTERN.finditer(
                    sentence
                )
            ]

            for medical_value in sentence_values:
                normalized_value = (
                    cls._compact_text(
                        medical_value
                    )
                )

                # Unsupported values are already separately reported.
                if (
                    normalized_value
                    not in normalized_all_sources
                ):
                    continue

                if not sentence_citations:
                    uncited_values.append(
                        medical_value
                    )
                    continue

                cited_source_text = "\n".join(
                    cls._source_text(
                        source_by_number[number]
                    )
                    for number
                    in sentence_citations
                    if number
                    in source_by_number
                )

                if (
                    normalized_value
                    not in cls._compact_text(
                        cited_source_text
                    )
                ):
                    misattributed_values.append(
                        medical_value
                    )

        if unsupported_values:
            issues.append(
                "unsupported_medical_value"
            )

        if uncited_values:
            issues.append(
                "uncited_medical_value"
            )

        if misattributed_values:
            issues.append(
                "misattributed_medical_value"
            )

        # Preserve stable order while removing duplicates.
        deduped_issues = tuple(
            dict.fromkeys(
                issues
            )
        )

        return GroundedResponseValidation(
            is_valid=not deduped_issues,
            issues=deduped_issues,
            unsupported_medical_values=tuple(
                dict.fromkeys(
                    unsupported_values
                )
            ),
            invalid_citation_numbers=tuple(
                invalid_citations
            ),
            uncited_medical_values=tuple(
                dict.fromkeys(
                    uncited_values
                )
            ),
            misattributed_medical_values=tuple(
                dict.fromkeys(
                    misattributed_values
                )
            ),
        )
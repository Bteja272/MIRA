import re


class ResponseValidationService:
    """
    Remove unsupported laboratory interpretation introduced by the
    language model.

    MIRA may report documented values, reference ranges, and flags.
    It must not independently determine whether a value is above,
    below, inside, or outside a range.
    """

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

    @staticmethod
    def _plain_text(
        value: str,
    ) -> str:
        """
        Remove common Markdown formatting before checking a sentence.
        """
        return re.sub(
            r"[*_`]",
            "",
            value,
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
        """
        Preserve Markdown lines while separating ordinary sentences.
        """
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
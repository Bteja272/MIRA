from __future__ import annotations

import re
from typing import Any

from evaluation.quality_corpus_loader import (
    RequiredFact,
)


CITATION_PATTERN = re.compile(
    r"\[\s*Source\s+(\d+)\s*\]",
    re.IGNORECASE,
)

_VALUE_END = r"(?=\s|[.,;:)\]\}]|$)"

MEDICAL_VALUE_PATTERNS = (
    # ISO dates.
    re.compile(
        r"\b20\d{2}-\d{2}-\d{2}\b"
    ),

    # ICD-style codes such as E11.9.
    re.compile(
        (
            r"\b[A-Z]\d{2}"
            r"(?:\.\d+)?\b"
        )
    ),

    # Blood pressure such as 132/84 mmHg.
    re.compile(
        (
            r"\b\d{2,3}/\d{2,3}"
            r"\s*mmHg"
            + _VALUE_END
        ),
        re.IGNORECASE,
    ),

    # Common medical values and durations.
    #
    # Do not use a trailing word boundary here because units such
    # as "%" end in a non-word character. A look-ahead correctly
    # handles values such as "7.2 %.".
    re.compile(
        (
            r"\b\d+(?:\.\d+)?\s*"
            r"(?:"
            r"mg/dL|mg|mmol/L|"
            r"mL/min/1\.73\s*m2|"
            r"mmHg|%|"
            r"days?|weeks?|months?"
            r")"
            + _VALUE_END
        ),
        re.IGNORECASE,
    ),
)


def compact_text(
    value: str,
) -> str:
    """
    Normalize text for deterministic exact-fact matching while
    ignoring whitespace differences.
    """
    return re.sub(
        r"\s+",
        "",
        (value or "").casefold(),
    )


def _compact_with_positions(
    value: str,
) -> tuple[str, list[int]]:
    """
    Return whitespace-free lowercase text plus a mapping from each
    normalized character back to its original string position.

    This lets citation proximity matching tolerate formatting
    differences such as "7.2%" versus "7.2 %".
    """
    normalized_characters: list[str] = []
    original_positions: list[int] = []

    for index, character in enumerate(
        value or ""
    ):
        if character.isspace():
            continue

        folded = character.casefold()

        for folded_character in folded:
            normalized_characters.append(
                folded_character
            )
            original_positions.append(
                index
            )

    return (
        "".join(
            normalized_characters
        ),
        original_positions,
    )


def fact_aliases(
    fact: RequiredFact,
) -> list[str]:
    aliases = [
        alias
        for alias in fact.aliases
        if alias.strip()
    ]

    if fact.text.strip():
        aliases.append(
            fact.text
        )

    seen: set[str] = set()
    result: list[str] = []

    for alias in aliases:
        normalized = compact_text(
            alias
        )

        if (
            normalized
            and normalized not in seen
        ):
            seen.add(
                normalized
            )
            result.append(
                alias
            )

    return result


def fact_is_present(
    *,
    answer: str,
    fact: RequiredFact,
) -> bool:
    normalized_answer = compact_text(
        answer
    )

    return any(
        compact_text(alias)
        in normalized_answer
        for alias in fact_aliases(
            fact
        )
    )


def nearby_citation_numbers(
    *,
    answer: str,
    fact: RequiredFact,
    before_characters: int = 80,
    after_characters: int = 220,
) -> set[int]:
    """
    Find source labels close to a required fact in the answer.

    Matching is performed on whitespace-free text, but source-label
    proximity is evaluated in the original answer so citation
    positions remain meaningful.
    """
    citations: set[int] = set()

    (
        normalized_answer,
        position_map,
    ) = _compact_with_positions(
        answer
    )

    if (
        not normalized_answer
        or not position_map
    ):
        return citations

    for alias in fact_aliases(
        fact
    ):
        normalized_alias = compact_text(
            alias
        )

        if not normalized_alias:
            continue

        search_start = 0

        while True:
            match_start = (
                normalized_answer.find(
                    normalized_alias,
                    search_start,
                )
            )

            if match_start == -1:
                break

            match_end = (
                match_start
                + len(
                    normalized_alias
                )
                - 1
            )

            original_start = (
                position_map[
                    match_start
                ]
            )

            original_end = (
                position_map[
                    match_end
                ]
                + 1
            )

            window_start = max(
                0,
                original_start
                - before_characters,
            )

            window_end = min(
                len(answer),
                original_end
                + after_characters,
            )

            window = answer[
                window_start:
                window_end
            ]

            citations.update(
                int(
                    citation_match
                    .group(1)
                )
                for citation_match
                in CITATION_PATTERN
                .finditer(
                    window
                )
            )

            search_start = (
                match_start + 1
            )

    return citations


def source_map(
    sources: list[dict[str, Any]],
) -> dict[int, dict[str, Any]]:
    mapped: dict[
        int,
        dict[str, Any],
    ] = {}

    for index, source in enumerate(
        sources,
        start=1,
    ):
        raw_number = source.get(
            "source_number",
            index,
        )

        try:
            number = int(
                raw_number
            )
        except (
            TypeError,
            ValueError,
        ):
            number = index

        mapped[number] = source

    return mapped


def source_supports_fact(
    *,
    source: dict[str, Any],
    fact: RequiredFact,
) -> bool:
    source_text = compact_text(
        str(
            source.get(
                "text",
                "",
            )
            or ""
        )
    )

    if not source_text:
        return False

    return any(
        compact_text(alias)
        in source_text
        for alias in fact_aliases(
            fact
        )
    )



def fact_is_grounded_in_sources(
    *,
    sources: list[dict[str, Any]],
    fact: RequiredFact,
) -> bool:
    """
    Grounding is independent from inline citation formatting.

    A required fact is grounded when at least one returned source from
    the expected document contains an accepted representation of it.
    """
    for source in sources:
        document_id = str(
            source.get(
                "document_id",
                "",
            )
            or ""
        )

        if (
            document_id
            not in fact.source_document_ids
        ):
            continue

        if source_supports_fact(
            source=source,
            fact=fact,
        ):
            return True

    return False

def cited_fact_is_supported(
    *,
    answer: str,
    sources: list[dict[str, Any]],
    fact: RequiredFact,
) -> bool:
    if not fact_is_present(
        answer=answer,
        fact=fact,
    ):
        return False

    mapped_sources = source_map(
        sources
    )

    citation_numbers = (
        nearby_citation_numbers(
            answer=answer,
            fact=fact,
        )
    )

    for number in citation_numbers:
        source = mapped_sources.get(
            number
        )

        if source is None:
            continue

        document_id = str(
            source.get(
                "document_id",
                "",
            )
            or ""
        )

        if (
            document_id
            not in fact
            .source_document_ids
        ):
            continue

        if source_supports_fact(
            source=source,
            fact=fact,
        ):
            return True

    return False


def citation_validity(
    *,
    answer: str,
    sources: list[dict[str, Any]],
) -> tuple[int, int]:
    mapped_sources = source_map(
        sources
    )

    citation_numbers = [
        int(match.group(1))
        for match
        in CITATION_PATTERN.finditer(
            answer
        )
    ]

    valid_count = sum(
        1
        for number
        in citation_numbers
        if number in mapped_sources
    )

    return (
        valid_count,
        len(citation_numbers),
    )


def extract_medical_values(
    value: str,
) -> list[str]:
    values: list[str] = []
    normalized_values: list[str] = []

    for pattern in (
        MEDICAL_VALUE_PATTERNS
    ):
        for match in pattern.finditer(
            value or ""
        ):
            candidate = (
                match.group(0)
                .strip()
            )

            normalized = (
                compact_text(
                    candidate
                )
            )

            if not normalized:
                continue

            # A broader earlier pattern may already have captured the
            # same claim, for example "132/84 mmHg" before "84 mmHg".
            if any(
                normalized
                in existing
                for existing
                in normalized_values
            ):
                continue

            contained_indices = [
                index
                for index, existing
                in enumerate(
                    normalized_values
                )
                if existing
                in normalized
            ]

            for index in reversed(
                contained_indices
            ):
                del values[index]
                del normalized_values[
                    index
                ]

            values.append(
                candidate
            )
            normalized_values.append(
                normalized
            )

    return values


def unsupported_medical_values(
    *,
    answer: str,
    sources: list[dict[str, Any]],
) -> list[str]:
    combined_source_text = (
        "\n".join(
            str(
                source.get(
                    "text",
                    "",
                )
                or ""
            )
            for source in sources
        )
    )

    normalized_sources = (
        compact_text(
            combined_source_text
        )
    )

    return [
        value
        for value
        in extract_medical_values(
            answer
        )
        if compact_text(
            value
        )
        not in normalized_sources
    ]
from __future__ import annotations

import re
from typing import Any, Iterator


IDENTITY_FIELDS = {
    "diagnoses": "name",
    "medications": "name",
    "lab_results": "test_name",
    "procedures": "name",
    "follow_up_instructions": (
        "instruction"
    ),
}


def normalize_value(
    value: Any,
) -> str:
    if value is None:
        return ""

    if hasattr(
        value,
        "value",
    ):
        value = value.value

    normalized = " ".join(
        str(value)
        .casefold()
        .split()
    )

    return normalized.strip(
        " \t\n\r.,;:"
    )


def value_matches(
    *,
    actual: Any,
    accepted_values: list[str],
) -> bool:
    actual_normalized = (
        normalize_value(
            actual
        )
    )

    if not actual_normalized:
        return False

    return any(
        actual_normalized
        == normalize_value(
            expected
        )
        for expected
        in accepted_values
    )


def evaluate_category(
    *,
    category: str,
    actual_items: list[dict[str, Any]],
    expected_items: list[
        dict[str, list[str]]
    ],
) -> dict:
    identity_field = (
        IDENTITY_FIELDS[
            category
        ]
    )

    unmatched_actual = set(
        range(
            len(actual_items)
        )
    )

    matched_pairs: list[
        tuple[
            dict[str, list[str]],
            dict[str, Any],
        ]
    ] = []

    unmatched_expected: list[
        dict[str, list[str]]
    ] = []

    for expected in expected_items:
        accepted_identity = (
            expected.get(
                identity_field,
                [],
            )
        )

        matched_index = None

        for index in sorted(
            unmatched_actual
        ):
            actual = (
                actual_items[
                    index
                ]
            )

            if value_matches(
                actual=actual.get(
                    identity_field
                ),
                accepted_values=(
                    accepted_identity
                ),
            ):
                matched_index = index
                break

        if matched_index is None:
            unmatched_expected.append(
                expected
            )
            continue

        unmatched_actual.remove(
            matched_index
        )

        matched_pairs.append(
            (
                expected,
                actual_items[
                    matched_index
                ],
            )
        )

    fact_tp = len(
        matched_pairs
    )
    fact_fn = len(
        unmatched_expected
    )
    fact_fp = len(
        unmatched_actual
    )

    field_tp = 0
    field_fp = 0
    field_fn = 0

    mismatches: list[dict] = []

    for expected, actual in (
        matched_pairs
    ):
        for (
            field_name,
            accepted_values,
        ) in expected.items():
            actual_value = (
                actual.get(
                    field_name
                )
            )

            if value_matches(
                actual=actual_value,
                accepted_values=(
                    accepted_values
                ),
            ):
                field_tp += 1

            else:
                field_fn += 1

                if normalize_value(
                    actual_value
                ):
                    field_fp += 1

                mismatches.append(
                    {
                        "identity": (
                            actual.get(
                                identity_field
                            )
                        ),
                        "field": (
                            field_name
                        ),
                        "actual": (
                            actual_value
                        ),
                        "accepted": (
                            accepted_values
                        ),
                    }
                )

    for expected in (
        unmatched_expected
    ):
        field_fn += len(
            expected
        )

        mismatches.append(
            {
                "identity": (
                    expected.get(
                        identity_field,
                        [""],
                    )[0]
                ),
                "field": "*missing_fact*",
                "actual": None,
                "accepted": (
                    expected
                ),
            }
        )

    evaluated_field_names = {
        field_name
        for expected
        in expected_items
        for field_name
        in expected.keys()
    }

    for index in unmatched_actual:
        actual = actual_items[
            index
        ]

        populated_fields = sum(
            1
            for field_name
            in evaluated_field_names
            if normalize_value(
                actual.get(
                    field_name
                )
            )
        )

        field_fp += max(
            1,
            populated_fields,
        )

        mismatches.append(
            {
                "identity": (
                    actual.get(
                        identity_field
                    )
                ),
                "field": "*unexpected_fact*",
                "actual": actual,
                "accepted": None,
            }
        )

    fact_precision = (
        fact_tp
        / (
            fact_tp
            + fact_fp
        )
        if (
            fact_tp
            + fact_fp
        )
        else 0.0
    )

    fact_recall = (
        fact_tp
        / (
            fact_tp
            + fact_fn
        )
        if (
            fact_tp
            + fact_fn
        )
        else 0.0
    )

    field_precision = (
        field_tp
        / (
            field_tp
            + field_fp
        )
        if (
            field_tp
            + field_fp
        )
        else 0.0
    )

    field_recall = (
        field_tp
        / (
            field_tp
            + field_fn
        )
        if (
            field_tp
            + field_fn
        )
        else 0.0
    )

    return {
        "fact_tp": fact_tp,
        "fact_fp": fact_fp,
        "fact_fn": fact_fn,
        "field_tp": field_tp,
        "field_fp": field_fp,
        "field_fn": field_fn,
        "fact_precision": round(
            fact_precision,
            6,
        ),
        "fact_recall": round(
            fact_recall,
            6,
        ),
        "field_precision": round(
            field_precision,
            6,
        ),
        "field_recall": round(
            field_recall,
            6,
        ),
        "mismatches": mismatches,
    }


def iter_evidence_dicts(
    value: Any,
) -> Iterator[dict[str, Any]]:
    if isinstance(
        value,
        dict,
    ):
        required_keys = {
            "document_id",
            "chunk_id",
            "chunk_index",
            "quoted_text",
        }

        if required_keys.issubset(
            value.keys()
        ):
            yield value
            return

        for nested in value.values():
            yield from (
                iter_evidence_dicts(
                    nested
                )
            )

        return

    if isinstance(
        value,
        list,
    ):
        for nested in value:
            yield from (
                iter_evidence_dicts(
                    nested
                )
            )


def normalize_evidence_text(
    value: str,
) -> str:
    return re.sub(
        r"\s+",
        " ",
        (value or "")
        .casefold()
        .strip(),
    )


def validate_evidence_refs(
    *,
    extraction_payload: dict[str, Any],
    document_id: str,
    chunks: list[dict[str, Any]],
) -> dict:
    chunk_map = {
        str(
            chunk["chunk_id"]
        ): chunk
        for chunk in chunks
    }

    valid_count = 0
    total_count = 0
    invalid: list[dict] = []

    for evidence in (
        iter_evidence_dicts(
            extraction_payload
        )
    ):
        total_count += 1

        chunk_id = str(
            evidence.get(
                "chunk_id",
                "",
            )
        )

        chunk = chunk_map.get(
            chunk_id
        )

        reason = None

        if (
            str(
                evidence.get(
                    "document_id",
                    "",
                )
            )
            != document_id
        ):
            reason = (
                "wrong_document"
            )

        elif chunk is None:
            reason = (
                "unknown_chunk"
            )

        elif (
            int(
                evidence.get(
                    "chunk_index",
                    -1,
                )
            )
            != int(
                chunk[
                    "chunk_index"
                ]
            )
        ):
            reason = (
                "wrong_chunk_index"
            )

        elif (
            evidence.get(
                "page_number"
            )
            != chunk.get(
                "page_number"
            )
        ):
            reason = (
                "wrong_page_number"
            )

        else:
            quote = (
                normalize_evidence_text(
                    str(
                        evidence.get(
                            "quoted_text",
                            "",
                        )
                    )
                )
            )

            source_text = (
                normalize_evidence_text(
                    str(
                        chunk.get(
                            "text",
                            "",
                        )
                    )
                )
            )

            if (
                not quote
                or quote
                not in source_text
            ):
                reason = (
                    "quote_not_in_chunk"
                )

        if reason is None:
            valid_count += 1
        else:
            invalid.append(
                {
                    "chunk_id": (
                        chunk_id
                    ),
                    "reason": reason,
                }
            )

    validity_rate = (
        valid_count
        / total_count
        if total_count
        else 1.0
    )

    return {
        "valid_count": valid_count,
        "total_count": total_count,
        "validity_rate": round(
            validity_rate,
            6,
        ),
        "invalid": invalid,
    }
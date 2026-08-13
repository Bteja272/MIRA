from __future__ import annotations


def recall_at_k(
    *,
    retrieved_chunk_ids: list[str],
    relevant_chunk_ids: set[str],
    k: int,
) -> float:
    if k <= 0:
        raise ValueError(
            "k must be greater than zero."
        )

    if not relevant_chunk_ids:
        return 0.0

    retrieved = set(
        retrieved_chunk_ids[:k]
    )

    return (
        len(
            retrieved
            & relevant_chunk_ids
        )
        / len(relevant_chunk_ids)
    )


def precision_at_k(
    *,
    retrieved_chunk_ids: list[str],
    relevant_chunk_ids: set[str],
    k: int,
) -> float:
    if k <= 0:
        raise ValueError(
            "k must be greater than zero."
        )

    top_k = retrieved_chunk_ids[:k]

    if not top_k:
        return 0.0

    relevant_count = sum(
        1
        for chunk_id in top_k
        if chunk_id
        in relevant_chunk_ids
    )

    # Use returned-result precision when a scoped corpus contains
    # fewer than k candidates.
    return (
        relevant_count
        / len(top_k)
    )


def reciprocal_rank(
    *,
    retrieved_chunk_ids: list[str],
    relevant_chunk_ids: set[str],
) -> float:
    if not relevant_chunk_ids:
        return 0.0

    for rank, chunk_id in enumerate(
        retrieved_chunk_ids,
        start=1,
    ):
        if chunk_id in relevant_chunk_ids:
            return 1.0 / rank

    return 0.0
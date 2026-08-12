from __future__ import annotations

import math
import re
from dataclasses import dataclass

from langchain_core.documents import (
    Document as LangChainDocument,
)


@dataclass(frozen=True)
class ContextOptimizationMetrics:
    input_document_count: int
    output_document_count: int

    input_characters: int
    output_characters: int

    input_estimated_tokens: int
    output_estimated_tokens: int

    token_budget: int
    truncated_document_count: int


@dataclass(frozen=True)
class ContextOptimizationResult:
    documents: list[LangChainDocument]
    metrics: ContextOptimizationMetrics


class ContextOptimizationService:
    """
    Apply deterministic context budgeting after document merge.

    The optimizer does not summarize or rewrite medical text. It only
    keeps source text verbatim up to a configured estimated-token
    budget so numerical values and clinical wording are not altered.
    """

    TOKEN_PATTERN = re.compile(
        r"\w+|[^\w\s]",
        re.UNICODE,
    )

    @classmethod
    def estimate_tokens(
        cls,
        text: str,
    ) -> int:
        cleaned = (
            text or ""
        ).strip()

        if not cleaned:
            return 0

        lexical_estimate = len(
            cls.TOKEN_PATTERN.findall(
                cleaned
            )
        )

        character_estimate = math.ceil(
            len(cleaned) / 4
        )

        return max(
            lexical_estimate,
            character_estimate,
        )

    @classmethod
    def _truncate_text(
        cls,
        text: str,
        token_budget: int,
    ) -> str:
        cleaned = (
            text or ""
        ).strip()

        if (
            not cleaned
            or token_budget <= 0
        ):
            return ""

        if (
            cls.estimate_tokens(
                cleaned
            )
            <= token_budget
        ):
            return cleaned

        low = 1
        high = len(cleaned)
        best = ""

        while low <= high:
            midpoint = (
                low + high
            ) // 2

            candidate = (
                cleaned[:midpoint]
                .rstrip()
            )

            if (
                cls.estimate_tokens(
                    candidate
                )
                <= token_budget
            ):
                best = candidate
                low = midpoint + 1

            else:
                high = midpoint - 1

        if not best:
            return ""

        boundary_start = max(
            0,
            len(best) - 120,
        )

        newline_index = best.rfind(
            "\n",
            boundary_start,
        )

        space_index = best.rfind(
            " ",
            boundary_start,
        )

        boundary_index = max(
            newline_index,
            space_index,
        )

        if boundary_index > 0:
            best = (
                best[:boundary_index]
                .rstrip()
            )

        return best

    @staticmethod
    def _allocate_token_budget(
        token_counts: list[int],
        total_budget: int,
    ) -> list[int]:
        if not token_counts:
            return []

        if total_budget <= 0:
            return [
                0
                for _ in token_counts
            ]

        if (
            sum(token_counts)
            <= total_budget
        ):
            return list(
                token_counts
            )

        allocations = [
            0
            for _ in token_counts
        ]

        remaining_indices = set(
            range(
                len(token_counts)
            )
        )

        remaining_budget = (
            total_budget
        )

        while remaining_indices:
            fair_share = (
                remaining_budget
                // len(
                    remaining_indices
                )
            )

            if fair_share <= 0:
                break

            completed_indices = [
                index
                for index
                in remaining_indices
                if token_counts[index]
                <= fair_share
            ]

            if completed_indices:
                for index in (
                    completed_indices
                ):
                    allocation = (
                        token_counts[index]
                    )
                    allocations[index] = (
                        allocation
                    )
                    remaining_budget -= (
                        allocation
                    )
                    remaining_indices.remove(
                        index
                    )

                continue

            for index in sorted(
                remaining_indices
            ):
                if remaining_budget <= 0:
                    break

                allocation = min(
                    fair_share,
                    remaining_budget,
                )

                allocations[index] = (
                    allocation
                )
                remaining_budget -= (
                    allocation
                )

            break

        if (
            remaining_budget > 0
            and remaining_indices
        ):
            for index in sorted(
                remaining_indices
            ):
                if remaining_budget <= 0:
                    break

                available = max(
                    0,
                    token_counts[index]
                    - allocations[index],
                )

                addition = min(
                    available,
                    remaining_budget,
                )

                allocations[index] += (
                    addition
                )
                remaining_budget -= (
                    addition
                )

        return allocations

    @classmethod
    def optimize(
        cls,
        *,
        documents: list[
            LangChainDocument
        ],
        token_budget: int,
    ) -> ContextOptimizationResult:
        if token_budget <= 0:
            raise ValueError(
                "token_budget must be "
                "greater than zero."
            )

        if not documents:
            metrics = (
                ContextOptimizationMetrics(
                    input_document_count=0,
                    output_document_count=0,
                    input_characters=0,
                    output_characters=0,
                    input_estimated_tokens=0,
                    output_estimated_tokens=0,
                    token_budget=(
                        token_budget
                    ),
                    truncated_document_count=0,
                )
            )

            return (
                ContextOptimizationResult(
                    documents=[],
                    metrics=metrics,
                )
            )

        original_texts = [
            (
                document
                .page_content
                .strip()
            )
            for document in documents
        ]

        token_counts = [
            cls.estimate_tokens(
                text
            )
            for text in original_texts
        ]

        allocations = (
            cls._allocate_token_budget(
                token_counts,
                token_budget,
            )
        )

        optimized_documents: list[
            LangChainDocument
        ] = []

        truncated_count = 0

        for (
            document,
            original_text,
            original_tokens,
            allocation,
        ) in zip(
            documents,
            original_texts,
            token_counts,
            allocations,
            strict=True,
        ):
            optimized_text = (
                cls._truncate_text(
                    original_text,
                    allocation,
                )
            )

            if not optimized_text:
                continue

            optimized_tokens = (
                cls.estimate_tokens(
                    optimized_text
                )
            )

            was_truncated = (
                optimized_text
                != original_text
            )

            if was_truncated:
                truncated_count += 1

            metadata = dict(
                document.metadata or {}
            )

            metadata.update(
                {
                    "context_original_estimated_tokens": (
                        original_tokens
                    ),
                    "context_estimated_tokens": (
                        optimized_tokens
                    ),
                    "context_truncated": (
                        was_truncated
                    ),
                }
            )

            optimized_documents.append(
                LangChainDocument(
                    page_content=(
                        optimized_text
                    ),
                    metadata=metadata,
                )
            )

        input_characters = sum(
            len(text)
            for text in original_texts
        )

        output_characters = sum(
            len(
                document.page_content
            )
            for document
            in optimized_documents
        )

        output_estimated_tokens = sum(
            cls.estimate_tokens(
                document.page_content
            )
            for document
            in optimized_documents
        )

        metrics = (
            ContextOptimizationMetrics(
                input_document_count=(
                    len(documents)
                ),
                output_document_count=(
                    len(
                        optimized_documents
                    )
                ),
                input_characters=(
                    input_characters
                ),
                output_characters=(
                    output_characters
                ),
                input_estimated_tokens=(
                    sum(token_counts)
                ),
                output_estimated_tokens=(
                    output_estimated_tokens
                ),
                token_budget=(
                    token_budget
                ),
                truncated_document_count=(
                    truncated_count
                ),
            )
        )

        return (
            ContextOptimizationResult(
                documents=(
                    optimized_documents
                ),
                metrics=metrics,
            )
        )
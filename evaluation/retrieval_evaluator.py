from __future__ import annotations

import statistics
from dataclasses import asdict
from time import perf_counter

from app.services.retrieval_service import (
    RetrievalService,
)
from evaluation.corpus_loader import (
    EvaluationCorpus,
    RetrievalCase,
)
from evaluation.retrieval_metrics import (
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
)


class RetrievalEvaluator:
    def __init__(
        self,
        *,
        corpus: EvaluationCorpus,
        ks: list[int],
    ) -> None:
        cleaned_ks = sorted(
            {
                int(k)
                for k in ks
                if int(k) > 0
            }
        )

        if not cleaned_ks:
            raise ValueError(
                "At least one positive k "
                "value is required."
            )

        self.corpus = corpus
        self.ks = cleaned_ks

    def warm_up(self) -> None:
        """
        Run one discarded retrieval so embedding/reranker model
        initialization does not distort measured case latency.
        """
        if not self.corpus.retrieval_cases:
            return

        case = self.corpus.retrieval_cases[0]

        RetrievalService.retrieve(
            query=case.query,
            top_k=max(self.ks),
            document_ids=(
                case.document_ids
            ),
            user_id=(
                self.corpus
                .evaluation_user[
                    "user_id"
                ]
            ),
        )

    def evaluate_case(
        self,
        case: RetrievalCase,
    ) -> dict:
        max_k = max(
            self.ks
        )

        started_at = perf_counter()

        results = (
            RetrievalService.retrieve(
                query=case.query,
                top_k=max_k,
                document_ids=(
                    case.document_ids
                ),
                user_id=(
                    self.corpus
                    .evaluation_user[
                        "user_id"
                    ]
                ),
            )
        )

        latency_ms = (
            perf_counter()
            - started_at
        ) * 1000

        retrieved_chunk_ids = [
            str(
                result.get(
                    "chunk_id",
                    "",
                )
            )
            for result in results
            if result.get(
                "chunk_id"
            )
        ]

        relevant_chunk_ids = set(
            case.relevant_chunk_ids
        )

        recall_scores = {
            str(k): round(
                recall_at_k(
                    retrieved_chunk_ids=(
                        retrieved_chunk_ids
                    ),
                    relevant_chunk_ids=(
                        relevant_chunk_ids
                    ),
                    k=k,
                ),
                6,
            )
            for k in self.ks
        }

        precision_scores = {
            str(k): round(
                precision_at_k(
                    retrieved_chunk_ids=(
                        retrieved_chunk_ids
                    ),
                    relevant_chunk_ids=(
                        relevant_chunk_ids
                    ),
                    k=k,
                ),
                6,
            )
            for k in self.ks
        }

        rr = round(
            reciprocal_rank(
                retrieved_chunk_ids=(
                    retrieved_chunk_ids
                ),
                relevant_chunk_ids=(
                    relevant_chunk_ids
                ),
            ),
            6,
        )

        return {
            "case": asdict(case),
            "retrieved_chunk_ids": (
                retrieved_chunk_ids
            ),
            "recall_at_k": (
                recall_scores
            ),
            "precision_at_k": (
                precision_scores
            ),
            "reciprocal_rank": rr,
            "latency_ms": round(
                latency_ms,
                3,
            ),
        }

    @staticmethod
    def _percentile(
        values: list[float],
        percentile: float,
    ) -> float:
        if not values:
            return 0.0

        ordered = sorted(
            values
        )

        if len(ordered) == 1:
            return ordered[0]

        position = (
            percentile
            * (
                len(ordered) - 1
            )
        )

        lower_index = int(
            position
        )

        upper_index = min(
            lower_index + 1,
            len(ordered) - 1,
        )

        fraction = (
            position
            - lower_index
        )

        return (
            ordered[lower_index]
            + (
                ordered[upper_index]
                - ordered[lower_index]
            )
            * fraction
        )

    def evaluate(self) -> dict:
        case_results = [
            self.evaluate_case(
                case
            )
            for case
            in self.corpus
            .retrieval_cases
        ]

        aggregate_recall: dict[
            str,
            float,
        ] = {}

        aggregate_precision: dict[
            str,
            float,
        ] = {}

        for k in self.ks:
            key = str(k)

            aggregate_recall[key] = round(
                statistics.fmean(
                    result[
                        "recall_at_k"
                    ][key]
                    for result
                    in case_results
                ),
                6,
            )

            aggregate_precision[key] = round(
                statistics.fmean(
                    result[
                        "precision_at_k"
                    ][key]
                    for result
                    in case_results
                ),
                6,
            )

        mrr = round(
            statistics.fmean(
                result[
                    "reciprocal_rank"
                ]
                for result
                in case_results
            ),
            6,
        )

        latencies = [
            float(
                result[
                    "latency_ms"
                ]
            )
            for result
            in case_results
        ]

        latency_summary = {
            "mean_ms": round(
                statistics.fmean(
                    latencies
                ),
                3,
            ),
            "median_ms": round(
                statistics.median(
                    latencies
                ),
                3,
            ),
            "p95_ms": round(
                self._percentile(
                    latencies,
                    0.95,
                ),
                3,
            ),
            "max_ms": round(
                max(latencies),
                3,
            ),
        }

        return {
            "corpus_version": (
                self.corpus.version
            ),
            "case_count": len(
                case_results
            ),
            "ks": self.ks,
            "aggregate": {
                "recall_at_k": (
                    aggregate_recall
                ),
                "precision_at_k": (
                    aggregate_precision
                ),
                "mrr": mrr,
                "latency": (
                    latency_summary
                ),
            },
            "cases": case_results,
        }
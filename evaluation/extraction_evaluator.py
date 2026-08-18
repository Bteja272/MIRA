from __future__ import annotations

import statistics
from time import perf_counter
from typing import Any

from app.schemas.medical_extraction import (
    MedicalDocumentExtraction,
)
from app.services.medical_extraction_service import (
    MedicalExtractionService,
)
from evaluation.corpus_loader import (
    EvaluationCorpus,
)
from evaluation.extraction_metrics import (
    evaluate_category,
    validate_evidence_refs,
)
from evaluation.quality_corpus_loader import (
    ExtractionCase,
    QualityCorpus,
)


class ExtractionEvaluator:
    def __init__(
        self,
        *,
        quality_corpus: QualityCorpus,
        retrieval_corpus: EvaluationCorpus,
        user_id: str,
    ) -> None:
        self.quality_corpus = (
            quality_corpus
        )
        self.retrieval_corpus = (
            retrieval_corpus
        )
        self.user_id = user_id

        self.documents = {
            str(
                document[
                    "document_id"
                ]
            ): document
            for document
            in retrieval_corpus.documents
        }

    def evaluate_case(
        self,
        case: ExtractionCase,
    ) -> dict:
        started_at = perf_counter()

        try:
            extraction = (
                MedicalExtractionService
                .extract(
                    document_id=(
                        case.document_id
                    ),
                    user_id=(
                        self.user_id
                    ),
                )
            )

            latency_ms = (
                perf_counter()
                - started_at
            ) * 1000

            payload = (
                extraction.model_dump(
                    mode="json"
                )
            )

            try:
                (
                    MedicalDocumentExtraction
                    .model_validate(
                        payload
                    )
                )
                schema_valid = True
                schema_error = None

            except Exception as exc:
                schema_valid = False
                schema_error = (
                    type(exc).__name__
                )

        except Exception as exc:
            latency_ms = (
                perf_counter()
                - started_at
            ) * 1000

            return {
                "case_id": (
                    case.case_id
                ),
                "document_id": (
                    case.document_id
                ),
                "schema_valid": False,
                "schema_error": (
                    type(exc).__name__
                ),
                "fact_precision": 0.0,
                "fact_recall": 0.0,
                "field_precision": 0.0,
                "field_recall": 0.0,
                "completeness": 0.0,
                "evidence_validity_rate": 0.0,
                "evidence_reference_count": 0,
                "latency_ms": round(
                    latency_ms,
                    3,
                ),
                "pass": False,
                "categories": {},
            }

        category_results: dict[
            str,
            dict,
        ] = {}

        fact_tp = 0
        fact_fp = 0
        fact_fn = 0
        field_tp = 0
        field_fp = 0
        field_fn = 0

        for category in (
            case.evaluated_categories
        ):
            actual_items = list(
                payload.get(
                    category,
                    [],
                )
                or []
            )

            expected_items = (
                case.expected.get(
                    category,
                    [],
                )
            )

            result = (
                evaluate_category(
                    category=category,
                    actual_items=(
                        actual_items
                    ),
                    expected_items=(
                        expected_items
                    ),
                )
            )

            category_results[
                category
            ] = result

            fact_tp += result[
                "fact_tp"
            ]
            fact_fp += result[
                "fact_fp"
            ]
            fact_fn += result[
                "fact_fn"
            ]
            field_tp += result[
                "field_tp"
            ]
            field_fp += result[
                "field_fp"
            ]
            field_fn += result[
                "field_fn"
            ]

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

        document = self.documents[
            case.document_id
        ]

        evidence = (
            validate_evidence_refs(
                extraction_payload=(
                    payload
                ),
                document_id=(
                    case.document_id
                ),
                chunks=list(
                    document[
                        "chunks"
                    ]
                ),
            )
        )

        case_pass = (
            schema_valid
            and fact_recall == 1.0
            and field_recall >= 0.90
            and evidence[
                "validity_rate"
            ]
            == 1.0
        )

        return {
            "case_id": case.case_id,
            "document_id": (
                case.document_id
            ),
            "schema_valid": (
                schema_valid
            ),
            "schema_error": (
                schema_error
            ),
            "status": payload.get(
                "status"
            ),
            "warning_codes": [
                warning.get(
                    "code"
                )
                for warning
                in payload.get(
                    "warnings",
                    [],
                )
                if isinstance(
                    warning,
                    dict,
                )
            ],
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
            "completeness": round(
                field_recall,
                6,
            ),
            "evidence_validity_rate": (
                evidence[
                    "validity_rate"
                ]
            ),
            "evidence_reference_count": (
                evidence[
                    "total_count"
                ]
            ),
            "invalid_evidence": (
                evidence[
                    "invalid"
                ]
            ),
            "latency_ms": round(
                latency_ms,
                3,
            ),
            "pass": case_pass,
            "categories": (
                category_results
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

        position = percentile * (
            len(ordered) - 1
        )

        lower = int(
            position
        )

        upper = min(
            lower + 1,
            len(ordered) - 1,
        )

        fraction = (
            position - lower
        )

        return (
            ordered[lower]
            + (
                ordered[upper]
                - ordered[lower]
            )
            * fraction
        )

    def evaluate(self) -> dict:
        results = [
            self.evaluate_case(
                case
            )
            for case
            in self.quality_corpus
            .extraction_cases
        ]

        if not results:
            return {
                "case_count": 0,
                "aggregate": {},
                "cases": [],
            }

        latencies = [
            float(
                result[
                    "latency_ms"
                ]
            )
            for result in results
        ]

        aggregate = {
            "schema_validity_rate": round(
                statistics.fmean(
                    1.0
                    if result[
                        "schema_valid"
                    ]
                    else 0.0
                    for result
                    in results
                ),
                6,
            ),
            "fact_precision": round(
                statistics.fmean(
                    result[
                        "fact_precision"
                    ]
                    for result
                    in results
                ),
                6,
            ),
            "fact_recall": round(
                statistics.fmean(
                    result[
                        "fact_recall"
                    ]
                    for result
                    in results
                ),
                6,
            ),
            "field_precision": round(
                statistics.fmean(
                    result[
                        "field_precision"
                    ]
                    for result
                    in results
                ),
                6,
            ),
            "field_recall": round(
                statistics.fmean(
                    result[
                        "field_recall"
                    ]
                    for result
                    in results
                ),
                6,
            ),
            "completeness": round(
                statistics.fmean(
                    result[
                        "completeness"
                    ]
                    for result
                    in results
                ),
                6,
            ),
            "evidence_validity_rate": round(
                statistics.fmean(
                    result[
                        "evidence_validity_rate"
                    ]
                    for result
                    in results
                ),
                6,
            ),
            "pass_rate": round(
                statistics.fmean(
                    1.0
                    if result["pass"]
                    else 0.0
                    for result in results
                ),
                6,
            ),
            "latency": {
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
            },
        }

        return {
            "case_count": len(
                results
            ),
            "aggregate": aggregate,
            "cases": results,
        }
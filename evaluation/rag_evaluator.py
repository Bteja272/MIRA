from __future__ import annotations

import statistics
from time import perf_counter

from app.services.rag_service import (
    RAGService,
)
from evaluation.corpus_loader import (
    EvaluationCorpus,
)
from evaluation.quality_corpus_loader import (
    QualityCorpus,
    RAGCase,
)
from evaluation.rag_metrics import (
    CITATION_PATTERN,
    citation_validity,
    cited_fact_is_supported,
    extract_medical_values,
    fact_is_grounded_in_sources,
    fact_is_present,
    unsupported_medical_values,
)


class RAGEvaluator:
    def __init__(
        self,
        *,
        corpus: QualityCorpus,
        retrieval_corpus: EvaluationCorpus,
        user_id: str,
    ) -> None:
        self.corpus = corpus
        self.user_id = user_id

        self.document_text_by_id = {
            str(
                document[
                    "document_id"
                ]
            ): "\n".join(
                str(
                    chunk.get(
                        "text",
                        "",
                    )
                )
                for chunk
                in document.get(
                    "chunks",
                    [],
                )
            )
            for document
            in retrieval_corpus.documents
        }

    def evaluate_case(
        self,
        case: RAGCase,
    ) -> dict:
        started_at = perf_counter()

        response = RAGService.query(
            query=case.query,
            document_ids=(
                case.document_ids
            ),
            user_id=self.user_id,
        )

        latency_ms = (
            perf_counter()
            - started_at
        ) * 1000

        answer = str(
            response.get(
                "answer",
                "",
            )
            or ""
        )

        sources = list(
            response.get(
                "sources",
                [],
            )
            or []
        )

        enriched_sources: list[
            dict
        ] = []

        for source in sources:
            enriched = dict(
                source
            )

            document_id = str(
                enriched.get(
                    "document_id",
                    "",
                )
                or ""
            )

            if not str(
                enriched.get(
                    "text",
                    "",
                )
                or ""
            ).strip():
                enriched["text"] = (
                    self
                    .document_text_by_id
                    .get(
                        document_id,
                        "",
                    )
                )

            enriched_sources.append(
                enriched
            )

        sources = enriched_sources

        fact_results: list[
            dict
        ] = []

        for fact in (
            case.required_facts
        ):
            present = fact_is_present(
                answer=answer,
                fact=fact,
            )

            grounded = (
                fact_is_grounded_in_sources(
                    sources=sources,
                    fact=fact,
                )
            )

            correctly_cited = (
                cited_fact_is_supported(
                    answer=answer,
                    sources=sources,
                    fact=fact,
                )
            )

            fact_results.append(
                {
                    "text": fact.text,
                    "source_document_ids": (
                        fact
                        .source_document_ids
                    ),
                    "present": present,
                    "grounded_in_returned_sources": (
                        grounded
                    ),
                    "correctly_cited_and_supported": (
                        correctly_cited
                    ),
                }
            )

        required_count = len(
            fact_results
        )

        present_count = sum(
            int(
                result["present"]
            )
            for result
            in fact_results
        )

        grounded_count = sum(
            int(
                result[
                    "grounded_in_returned_sources"
                ]
            )
            for result
            in fact_results
        )

        cited_supported_count = sum(
            int(
                result[
                    "correctly_cited_and_supported"
                ]
            )
            for result
            in fact_results
        )

        valid_citations, total_citations = (
            citation_validity(
                answer=answer,
                sources=sources,
            )
        )

        unsupported_values = (
            unsupported_medical_values(
                answer=answer,
                sources=sources,
            )
        )

        answer_medical_values = (
            extract_medical_values(
                answer
            )
        )

        medical_value_count = len(
            answer_medical_values
        )

        fact_recall = (
            present_count
            / required_count
            if required_count
            else 0.0
        )

        grounded_fact_rate = (
            grounded_count
            / required_count
            if required_count
            else 0.0
        )

        citation_attribution_rate = (
            cited_supported_count
            / required_count
            if required_count
            else 0.0
        )

        citation_validity_rate = (
            valid_citations
            / total_citations
            if total_citations
            else 0.0
        )

        unsupported_value_rate = (
            len(unsupported_values)
            / medical_value_count
            if medical_value_count
            else 0.0
        )

        case_pass = (
            fact_recall == 1.0
            and grounded_fact_rate
            == 1.0
            and citation_attribution_rate
            == 1.0
            and citation_validity_rate
            == 1.0
            and unsupported_value_rate
            == 0.0
        )

        return {
            "case_id": case.case_id,
            "answer": answer,
            "sources": sources,
            "document_ids": (
                case.document_ids
            ),
            "required_fact_recall": round(
                fact_recall,
                6,
            ),
            "grounded_required_fact_rate": round(
                grounded_fact_rate,
                6,
            ),
            "citation_attribution_rate": round(
                citation_attribution_rate,
                6,
            ),
            "citation_validity_rate": round(
                citation_validity_rate,
                6,
            ),
            "citation_count": (
                total_citations
            ),
            "unsupported_medical_value_rate": round(
                unsupported_value_rate,
                6,
            ),
            "unsupported_medical_values": (
                unsupported_values
            ),
            "medical_value_claim_count": (
                medical_value_count
            ),
            "source_count": len(
                sources
            ),
            "latency_ms": round(
                latency_ms,
                3,
            ),
            "pass": case_pass,
            "facts": fact_results,
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
            in self.corpus.rag_cases
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
            "required_fact_recall": round(
                statistics.fmean(
                    result[
                        "required_fact_recall"
                    ]
                    for result
                    in results
                ),
                6,
            ),
            "grounded_required_fact_rate": round(
                statistics.fmean(
                    result[
                        "grounded_required_fact_rate"
                    ]
                    for result
                    in results
                ),
                6,
            ),
            "citation_attribution_rate": round(
                statistics.fmean(
                    result[
                        "citation_attribution_rate"
                    ]
                    for result
                    in results
                ),
                6,
            ),
            "citation_validity_rate": round(
                statistics.fmean(
                    result[
                        "citation_validity_rate"
                    ]
                    for result
                    in results
                ),
                6,
            ),
            "unsupported_medical_value_rate": round(
                statistics.fmean(
                    result[
                        "unsupported_medical_value_rate"
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
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from evaluation.dataset_loader import (
    load_rag_eval_dataset,
)
from evaluation.metrics import (
    aggregate_retrieval_results,
)
from evaluation.models import (
    ContextCaseResult,
    RAGEvalCase,
    RetrievalCaseResult,
)
from evaluation.reporting import (
    dataclass_list,
    write_json_report,
)

from app.services.context_optimization_service import (
    ContextOptimizationService,
)
from app.services.document_merge_service import (
    DocumentMergeService,
)
from app.services.document_service import (
    DocumentService,
)
from app.services.langchain_retriever_service import (
    LangChainRetrieverService,
)


DEFAULT_DATASET_PATH = (
    Path(__file__).resolve().parent
    / "datasets"
    / "rag_eval_cases.json"
)

DEFAULT_REPORT_DIRECTORY = (
    Path(__file__).resolve().parent
    / "reports"
)


class LiveRetrievalRunner:
    def __init__(
        self,
        *,
        user_id: str | None,
        top_k: int,
        context_token_budget: int,
    ) -> None:
        if top_k <= 0:
            raise ValueError(
                "top_k must be greater than zero."
            )

        if context_token_budget <= 0:
            raise ValueError(
                "context_token_budget must be "
                "greater than zero."
            )

        self.user_id = user_id
        self.top_k = top_k
        self.context_token_budget = (
            context_token_budget
        )

    def _document_id_map(
        self,
    ) -> dict[str, str]:
        documents = (
            DocumentService.list_documents(
                user_id=self.user_id
            )
        )

        filename_to_ids: dict[
            str,
            list[str],
        ] = {}

        for document in documents:
            filename = str(
                document.get(
                    "filename",
                    "",
                )
            ).strip()

            document_id = str(
                document.get(
                    "document_id",
                    "",
                )
            ).strip()

            if (
                not filename
                or not document_id
            ):
                continue

            filename_to_ids.setdefault(
                filename,
                [],
            ).append(
                document_id
            )

        duplicates = {
            filename: ids
            for filename, ids
            in filename_to_ids.items()
            if len(ids) > 1
        }

        if duplicates:
            duplicate_names = ", ".join(
                sorted(
                    duplicates
                )
            )

            raise RuntimeError(
                "Duplicate evaluation filenames "
                "exist for this user: "
                f"{duplicate_names}"
            )

        return {
            filename: ids[0]
            for filename, ids
            in filename_to_ids.items()
        }

    @staticmethod
    def _resolve_case_document_ids(
        *,
        case: RAGEvalCase,
        document_id_map: dict[
            str,
            str,
        ],
    ) -> list[str]:
        missing = [
            filename
            for filename
            in case.documents
            if filename
            not in document_id_map
        ]

        if missing:
            raise RuntimeError(
                f"{case.case_id}: missing "
                "evaluation documents: "
                + ", ".join(
                    missing
                )
            )

        return [
            document_id_map[
                filename
            ]
            for filename
            in case.documents
        ]

    def _retrieve_for_case(
        self,
        *,
        case: RAGEvalCase,
        document_ids: list[str],
    ):
        if case.task == "comparison":
            return (
                LangChainRetrieverService
                .retrieve_documents(
                    document_ids=(
                        document_ids
                    ),
                    user_id=self.user_id,
                )
            )

        if (
            case.task
            == "summarization"
        ):
            if len(document_ids) != 1:
                raise RuntimeError(
                    f"{case.case_id}: "
                    "summarization requires "
                    "exactly one document."
                )

            return (
                LangChainRetrieverService
                .retrieve_document(
                    document_id=(
                        document_ids[0]
                    ),
                    user_id=self.user_id,
                )
            )

        return (
            LangChainRetrieverService
            .retrieve(
                query=case.query,
                top_k=self.top_k,
                document_ids=(
                    document_ids
                ),
                user_id=self.user_id,
            )
        )

    def run(
        self,
        *,
        dataset_path: (
            str | Path
        ) = DEFAULT_DATASET_PATH,
    ) -> dict[str, Any]:
        from evaluation.retrieval_evaluator import (
            RetrievalEvaluator,
        )

        dataset = (
            load_rag_eval_dataset(
                dataset_path
            )
        )

        document_id_map = (
            self._document_id_map()
        )

        expected_filenames = {
            filename
            for case in dataset.cases
            for filename in case.documents
        }

        missing_globally = sorted(
            filename
            for filename
            in expected_filenames
            if filename
            not in document_id_map
        )

        if missing_globally:
            raise RuntimeError(
                "Missing required synthetic "
                "evaluation documents: "
                + ", ".join(
                    missing_globally
                )
            )

        retrieval_results: list[
            RetrievalCaseResult
        ] = []

        context_results: list[
            ContextCaseResult
        ] = []

        per_case: list[dict[str, Any]] = []

        for case in dataset.cases:
            document_ids = (
                self
                ._resolve_case_document_ids(
                    case=case,
                    document_id_map=(
                        document_id_map
                    ),
                )
            )

            retrieved_documents = (
                self._retrieve_for_case(
                    case=case,
                    document_ids=(
                        document_ids
                    ),
                )
            )

            if case.task == "qa":
                retrieval_result = (
                    RetrievalEvaluator
                    .evaluate_ranked_retrieval(
                        case=case,
                        documents=(
                            retrieved_documents
                        ),
                        k=self.top_k,
                    )
                )

                retrieval_results.append(
                    retrieval_result
                )

            merged_documents = (
                DocumentMergeService
                .merge_documents(
                    retrieved_documents
                )
            )

            optimized = (
                ContextOptimizationService
                .optimize(
                    documents=(
                        merged_documents
                    ),
                    token_budget=(
                        self
                        .context_token_budget
                    ),
                )
            )

            context_result = (
                RetrievalEvaluator
                .evaluate_context(
                    case=case,
                    documents=(
                        optimized.documents
                    ),
                )
            )

            context_results.append(
                context_result
            )

            per_case.append(
                {
                    "case_id": (
                        case.case_id
                    ),
                    "task": case.task,
                    "query": case.query,
                    "document_ids": (
                        document_ids
                    ),
                    "retrieved_count": (
                        len(
                            retrieved_documents
                        )
                    ),
                    "retrieved_sources": [
                        (
                            document.metadata
                            or {}
                        ).get(
                            "source"
                        )
                        for document
                        in retrieved_documents
                    ],
                    "context_metrics": {
                        "input_document_count": (
                            optimized
                            .metrics
                            .input_document_count
                        ),
                        "output_document_count": (
                            optimized
                            .metrics
                            .output_document_count
                        ),
                        "input_estimated_tokens": (
                            optimized
                            .metrics
                            .input_estimated_tokens
                        ),
                        "output_estimated_tokens": (
                            optimized
                            .metrics
                            .output_estimated_tokens
                        ),
                        "token_budget": (
                            optimized
                            .metrics
                            .token_budget
                        ),
                        "truncated_document_count": (
                            optimized
                            .metrics
                            .truncated_document_count
                        ),
                    },
                    "context_result": {
                        "document_recall": (
                            context_result
                            .document_recall
                        ),
                        "required_fact_survival_rate": (
                            context_result
                            .required_fact_survival_rate
                        ),
                        "expected_evidence_retained": (
                            context_result
                            .expected_evidence_retained
                        ),
                    },
                }
            )

        context_document_recall = (
            sum(
                result.document_recall
                for result
                in context_results
            )
            / len(context_results)
            if context_results
            else 0.0
        )

        fact_survival_rate = (
            sum(
                result
                .required_fact_survival_rate
                for result
                in context_results
            )
            / len(context_results)
            if context_results
            else 0.0
        )

        evidence_retention_rate = (
            sum(
                1.0
                if result
                .expected_evidence_retained
                else 0.0
                for result
                in context_results
            )
            / len(context_results)
            if context_results
            else 0.0
        )

        return {
            "dataset_name": (
                dataset.dataset_name
            ),
            "dataset_version": (
                dataset.dataset_version
            ),
            "user_id": self.user_id,
            "top_k": self.top_k,
            "context_token_budget": (
                self.context_token_budget
            ),
            "retrieval": (
                aggregate_retrieval_results(
                    retrieval_results
                )
            ),
            "context": {
                "case_count": (
                    len(
                        context_results
                    )
                ),
                "document_recall": (
                    context_document_recall
                ),
                "required_fact_survival_rate": (
                    fact_survival_rate
                ),
                "evidence_retention_rate": (
                    evidence_retention_rate
                ),
            },
            "retrieval_cases": (
                dataclass_list(
                    retrieval_results
                )
            ),
            "context_cases": (
                dataclass_list(
                    context_results
                )
            ),
            "cases": per_case,
        }


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Run MIRA live retrieval "
            "evaluation against indexed "
            "synthetic documents."
        )
    )

    parser.add_argument(
        "--user-id",
        default=None,
        help=(
            "MIRA user_id that owns the "
            "synthetic evaluation documents."
        ),
    )

    parser.add_argument(
        "--top-k",
        type=int,
        default=3,
    )

    parser.add_argument(
        "--context-token-budget",
        type=int,
        default=12000,
    )

    parser.add_argument(
        "--dataset",
        default=str(
            DEFAULT_DATASET_PATH
        ),
    )

    parser.add_argument(
        "--report-directory",
        default=str(
            DEFAULT_REPORT_DIRECTORY
        ),
    )

    args = parser.parse_args()

    runner = LiveRetrievalRunner(
        user_id=args.user_id,
        top_k=args.top_k,
        context_token_budget=(
            args.context_token_budget
        ),
    )

    report = runner.run(
        dataset_path=args.dataset
    )

    output_path = write_json_report(
        report=report,
        output_directory=(
            args.report_directory
        ),
    )

    retrieval = report[
        "retrieval"
    ]
    context = report[
        "context"
    ]

    print(
        "MIRA Live RAG Retrieval Evaluation"
    )
    print(
        "=================================="
    )
    print(
        f"Dataset: "
        f"{report['dataset_name']} "
        f"{report['dataset_version']}"
    )
    print(
        f"Top K: {report['top_k']}"
    )
    print(
        f"QA cases: "
        f"{retrieval['case_count']}"
    )
    print(
        "Hit Rate@K: "
        f"{retrieval['hit_rate_at_k']:.3f}"
    )
    print(
        "Recall@K: "
        f"{retrieval['recall_at_k']:.3f}"
    )
    print(
        "MRR: "
        f"{retrieval['mrr']:.3f}"
    )
    print(
        "Wrong-document rate: "
        f"{retrieval['wrong_document_rate']:.3f}"
    )
    print(
        "Context document recall: "
        f"{context['document_recall']:.3f}"
    )
    print(
        "Required-fact survival: "
        f"{context['required_fact_survival_rate']:.3f}"
    )
    print(
        "Evidence retention: "
        f"{context['evidence_retention_rate']:.3f}"
    )
    print(
        f"Report: {output_path}"
    )


if __name__ == "__main__":
    main()

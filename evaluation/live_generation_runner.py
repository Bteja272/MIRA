from __future__ import annotations

import argparse
from dataclasses import asdict
from pathlib import Path
from typing import Any

from evaluation.dataset_loader import load_rag_eval_dataset
from evaluation.generation_evaluator import (
    GenerationEvaluator,
    aggregate_generation_results,
)
from evaluation.reporting import write_json_report

from app.services.context_optimization_service import (
    ContextOptimizationService,
)
from app.services.document_merge_service import (
    DocumentMergeService,
)
from app.services.document_service import DocumentService
from app.services.langchain_retriever_service import (
    LangChainRetrieverService,
)
from app.services.llm_service import LLMService
from app.services.prompt_service import PromptService
from app.services.response_validation_service import (
    ResponseValidationService,
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


class LiveGenerationRunner:
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
                "context_token_budget must be greater than zero."
            )

        self.user_id = user_id
        self.top_k = top_k
        self.context_token_budget = context_token_budget

    def _document_id_map(self) -> dict[str, str]:
        documents = DocumentService.list_documents(
            user_id=self.user_id
        )

        filename_to_ids: dict[str, list[str]] = {}

        for document in documents:
            filename = str(
                document.get("filename", "")
            ).strip()
            document_id = str(
                document.get("document_id", "")
            ).strip()

            if not filename or not document_id:
                continue

            filename_to_ids.setdefault(
                filename,
                [],
            ).append(document_id)

        duplicates = {
            filename: ids
            for filename, ids
            in filename_to_ids.items()
            if len(ids) > 1
        }

        if duplicates:
            raise RuntimeError(
                "Duplicate evaluation filenames exist for this user: "
                + ", ".join(sorted(duplicates))
            )

        return {
            filename: ids[0]
            for filename, ids
            in filename_to_ids.items()
        }

    @staticmethod
    def _resolve_case_document_ids(
        *,
        case,
        document_id_map: dict[str, str],
    ) -> list[str]:
        missing = [
            filename
            for filename in case.documents
            if filename not in document_id_map
        ]

        if missing:
            raise RuntimeError(
                f"{case.case_id}: missing evaluation documents: "
                + ", ".join(missing)
            )

        return [
            document_id_map[filename]
            for filename in case.documents
        ]

    def _retrieve_for_case(
        self,
        *,
        case,
        document_ids: list[str],
    ):
        if case.task == "comparison":
            return (
                LangChainRetrieverService
                .retrieve_documents(
                    document_ids=document_ids,
                    user_id=self.user_id,
                )
            )

        if case.task == "summarization":
            if len(document_ids) != 1:
                raise RuntimeError(
                    f"{case.case_id}: summarization requires exactly one document."
                )

            return (
                LangChainRetrieverService
                .retrieve_document(
                    document_id=document_ids[0],
                    user_id=self.user_id,
                )
            )

        return (
            LangChainRetrieverService.retrieve(
                query=case.query,
                top_k=self.top_k,
                document_ids=document_ids,
                user_id=self.user_id,
            )
        )

    def run(
        self,
        *,
        dataset_path: str | Path = DEFAULT_DATASET_PATH,
    ) -> dict[str, Any]:
        dataset = load_rag_eval_dataset(
            dataset_path
        )

        document_id_map = self._document_id_map()

        generation_results = []
        grounded_passes = 0
        unsupported_value_cases = 0
        invalid_citation_cases = 0
        uncited_value_cases = 0
        misattributed_value_cases = 0
        per_case: list[dict[str, Any]] = []

        for case in dataset.cases:
            document_ids = (
                self._resolve_case_document_ids(
                    case=case,
                    document_id_map=document_id_map,
                )
            )

            retrieved = self._retrieve_for_case(
                case=case,
                document_ids=document_ids,
            )

            merged = (
                DocumentMergeService.merge_documents(
                    retrieved
                )
            )

            optimized = (
                ContextOptimizationService.optimize(
                    documents=merged,
                    token_budget=(
                        self.context_token_budget
                    ),
                )
            )

            prompt = PromptService.build_prompt(
                query=case.query,
                documents=optimized.documents,
                task=case.task,
            )

            generation = (
                LLMService
                .generate_response_with_metadata(
                    prompt=prompt
                )
            )

            answer = generation.text

            sources = (
                LangChainRetrieverService
                .to_source_dicts(
                    optimized.documents
                )
            )

            grounded = (
                ResponseValidationService
                .validate_grounded_answer(
                    answer=answer,
                    sources=sources,
                )
            )

            evaluated = (
                GenerationEvaluator.evaluate(
                    case=case,
                    answer=answer,
                    grounded_is_valid=(
                        grounded.is_valid
                    ),
                )
            )

            generation_results.append(
                evaluated
            )

            grounded_passes += int(
                grounded.is_valid
            )
            unsupported_value_cases += int(
                bool(
                    grounded
                    .unsupported_medical_values
                )
            )
            invalid_citation_cases += int(
                bool(
                    grounded
                    .invalid_citation_numbers
                )
            )
            uncited_value_cases += int(
                bool(
                    grounded
                    .uncited_medical_values
                )
            )
            misattributed_value_cases += int(
                bool(
                    grounded
                    .misattributed_medical_values
                )
            )

            per_case.append(
                {
                    "case_id": case.case_id,
                    "task": case.task,
                    "query": case.query,
                    "answer": answer,
                    "sources": sources,
                    "generation": {
                        "primary_provider": (
                            generation
                            .metadata
                            .primary_provider
                        ),
                        "provider": (
                            generation
                            .metadata
                            .provider
                        ),
                        "model": (
                            generation
                            .metadata
                            .model
                        ),
                        "attempts": (
                            generation
                            .metadata
                            .attempts
                        ),
                        "fallback_used": (
                            generation
                            .metadata
                            .fallback_used
                        ),
                        "total_latency_ms": (
                            generation
                            .metadata
                            .total_latency_ms
                        ),
                    },
                    "grounding": {
                        "is_valid": grounded.is_valid,
                        "issues": list(
                            grounded.issues
                        ),
                        "unsupported_medical_values": list(
                            grounded
                            .unsupported_medical_values
                        ),
                        "invalid_citation_numbers": list(
                            grounded
                            .invalid_citation_numbers
                        ),
                        "uncited_medical_values": list(
                            grounded
                            .uncited_medical_values
                        ),
                        "misattributed_medical_values": list(
                            grounded
                            .misattributed_medical_values
                        ),
                    },
                    "evaluation": asdict(
                        evaluated
                    ),
                }
            )

        summary = aggregate_generation_results(
            generation_results
        )

        case_count = len(
            generation_results
        )

        summary.update(
            {
                "grounded_answer_pass_rate": (
                    grounded_passes / case_count
                    if case_count
                    else 0.0
                ),
                "unsupported_medical_value_rate": (
                    unsupported_value_cases
                    / case_count
                    if case_count
                    else 0.0
                ),
                "invalid_citation_rate": (
                    invalid_citation_cases
                    / case_count
                    if case_count
                    else 0.0
                ),
                "uncited_medical_value_rate": (
                    uncited_value_cases
                    / case_count
                    if case_count
                    else 0.0
                ),
                "misattributed_medical_value_rate": (
                    misattributed_value_cases
                    / case_count
                    if case_count
                    else 0.0
                ),
            }
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
            "generation_summary": summary,
            "cases": per_case,
        }


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Run MIRA live generation and grounding evaluation."
        )
    )

    parser.add_argument(
        "--user-id",
        default=None,
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

    runner = LiveGenerationRunner(
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
        prefix="rag_generation_eval",
    )

    summary = report[
        "generation_summary"
    ]

    print(
        "MIRA Live RAG Generation Evaluation"
    )
    print(
        "==================================="
    )
    print(
        f"Dataset: "
        f"{report['dataset_name']} "
        f"{report['dataset_version']}"
    )
    print(
        f"Cases: "
        f"{summary['case_count']}"
    )
    print(
        "Required Fact Recall: "
        f"{summary['required_fact_recall']:.3f}"
    )
    print(
        "Forbidden Fact Violation Rate: "
        f"{summary['forbidden_fact_violation_rate']:.3f}"
    )
    print(
        "Abstention Accuracy: "
        f"{summary['abstention_accuracy']:.3f}"
    )
    print(
        "Grounded Answer Pass Rate: "
        f"{summary['grounded_answer_pass_rate']:.3f}"
    )
    print(
        "Unsupported Medical Value Rate: "
        f"{summary['unsupported_medical_value_rate']:.3f}"
    )
    print(
        "Invalid Citation Rate: "
        f"{summary['invalid_citation_rate']:.3f}"
    )
    print(
        "Uncited Medical Value Rate: "
        f"{summary['uncited_medical_value_rate']:.3f}"
    )
    print(
        "Misattributed Medical Value Rate: "
        f"{summary['misattributed_medical_value_rate']:.3f}"
    )
    print(
        "Case Pass Rate: "
        f"{summary['case_pass_rate']:.3f}"
    )
    print(
        f"Report: {output_path}"
    )


if __name__ == "__main__":
    main()

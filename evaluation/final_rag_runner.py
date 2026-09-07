from __future__ import annotations

import argparse
from dataclasses import asdict
from pathlib import Path
from typing import Any

from evaluation.dataset_loader import (
    load_rag_eval_dataset,
)
from evaluation.generation_evaluator import (
    GenerationEvaluator,
    aggregate_generation_results,
)
from evaluation.reporting import (
    write_json_report,
)

from app.services.document_service import (
    DocumentService,
)
from app.services.rag_service import (
    RAGService,
)
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


class FinalRAGRunner:
    """
    Evaluate the final production-equivalent RAG output.

    Unlike the raw generation runner, this calls RAGService.query()
    directly so the benchmark includes MIRA's normal retrieval,
    document merge, context optimization, prompting, sanitization,
    grounding validation, constrained repair, deterministic fallback,
    and final disclaimer handling.
    """

    def __init__(
        self,
        *,
        user_id: str | None,
    ) -> None:
        self.user_id = user_id

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
            raise RuntimeError(
                "Duplicate evaluation filenames "
                "exist for this user: "
                + ", ".join(
                    sorted(duplicates)
                )
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

    @staticmethod
    def _normalize_sources(
        sources: Any,
    ) -> list[dict]:
        if not isinstance(
            sources,
            list,
        ):
            return []

        normalized: list[dict] = []

        for index, source in enumerate(
            sources,
            start=1,
        ):
            if not isinstance(
                source,
                dict,
            ):
                continue

            copied = dict(
                source
            )

            copied.setdefault(
                "source_number",
                index,
            )

            normalized.append(
                copied
            )

        return normalized

    def run(
        self,
        *,
        dataset_path: (
            str | Path
        ) = DEFAULT_DATASET_PATH,
    ) -> dict[str, Any]:
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

        generation_results = []

        grounded_passes = 0
        missing_source_citation_cases = 0
        unsupported_value_cases = 0
        invalid_citation_cases = 0
        uncited_value_cases = 0
        misattributed_value_cases = 0

        per_case: list[
            dict[str, Any]
        ] = []

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

            result = RAGService.query(
                query=case.query,
                document_ids=document_ids,
                user_id=self.user_id,
            )

            if not isinstance(
                result,
                dict,
            ):
                raise RuntimeError(
                    f"{case.case_id}: "
                    "RAGService.query() did not "
                    "return a dictionary."
                )

            answer = str(
                result.get(
                    "answer",
                    "",
                )
                or ""
            ).strip()

            sources = (
                self._normalize_sources(
                    result.get(
                        "sources",
                        [],
                    )
                )
            )

            grounding = (
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
                        grounding.is_valid
                    ),
                )
            )

            generation_results.append(
                evaluated
            )

            grounded_passes += int(
                grounding.is_valid
            )

            missing_source_citation_cases += int(
                "missing_source_citation"
                in grounding.issues
            )

            unsupported_value_cases += int(
                bool(
                    grounding
                    .unsupported_medical_values
                )
            )

            invalid_citation_cases += int(
                bool(
                    grounding
                    .invalid_citation_numbers
                )
            )

            uncited_value_cases += int(
                bool(
                    grounding
                    .uncited_medical_values
                )
            )

            misattributed_value_cases += int(
                bool(
                    grounding
                    .misattributed_medical_values
                )
            )

            per_case.append(
                {
                    "case_id": (
                        case.case_id
                    ),
                    "task": case.task,
                    "query": case.query,
                    "answer": answer,
                    "document_ids": (
                        document_ids
                    ),
                    "route": result.get(
                        "route",
                        "rag",
                    ),
                    "latency_seconds": (
                        result.get(
                            "latency_seconds"
                        )
                    ),
                    "selected_document_count": (
                        result.get(
                            "selected_document_count"
                        )
                    ),
                    "sources": sources,
                    "grounding": {
                        "is_valid": (
                            grounding.is_valid
                        ),
                        "issues": list(
                            grounding.issues
                        ),
                        "unsupported_medical_values": list(
                            grounding
                            .unsupported_medical_values
                        ),
                        "invalid_citation_numbers": list(
                            grounding
                            .invalid_citation_numbers
                        ),
                        "uncited_medical_values": list(
                            grounding
                            .uncited_medical_values
                        ),
                        "misattributed_medical_values": list(
                            grounding
                            .misattributed_medical_values
                        ),
                    },
                    "evaluation": (
                        asdict(
                            evaluated
                        )
                    ),
                }
            )

        summary = (
            aggregate_generation_results(
                generation_results
            )
        )

        case_count = len(
            generation_results
        )

        summary.update(
            {
                "grounded_answer_pass_rate": (
                    grounded_passes
                    / case_count
                    if case_count
                    else 0.0
                ),
                "missing_source_citation_rate": (
                    missing_source_citation_cases
                    / case_count
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
            "evaluation_mode": (
                "final_production_rag"
            ),
            "user_id": self.user_id,
            "generation_summary": (
                summary
            ),
            "cases": per_case,
        }


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Run MIRA final production-"
            "equivalent RAG evaluation."
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

    runner = FinalRAGRunner(
        user_id=args.user_id
    )

    report = runner.run(
        dataset_path=args.dataset
    )

    output_path = (
        write_json_report(
            report=report,
            output_directory=(
                args.report_directory
            ),
            prefix=(
                "rag_final_eval"
            ),
        )
    )

    summary = report[
        "generation_summary"
    ]

    print(
        "MIRA Final Production RAG Evaluation"
    )
    print(
        "===================================="
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
        "Missing Source Citation Rate: "
        f"{summary['missing_source_citation_rate']:.3f}"
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

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from evaluation.end_to_end_evaluator import (
    EndToEndEvaluator,
    aggregate_end_to_end_results,
)
from evaluation.reporting import (
    write_json_report,
)


DEFAULT_REPORT_DIRECTORY = (
    Path(__file__).resolve().parent
    / "reports"
)


def _load_json(
    path: str | Path,
) -> dict[str, Any]:
    report_path = Path(
        path
    )

    if not report_path.exists():
        raise FileNotFoundError(
            "Report not found: "
            f"{report_path}"
        )

    with report_path.open(
        "r",
        encoding="utf-8",
    ) as handle:
        value = json.load(
            handle
        )

    if not isinstance(
        value,
        dict,
    ):
        raise ValueError(
            "Report must contain a "
            "JSON object: "
            f"{report_path}"
        )

    return value


def _validate_dataset_identity(
    *,
    retrieval_report: dict[
        str,
        Any,
    ],
    final_report: dict[
        str,
        Any,
    ],
) -> None:
    retrieval_name = (
        retrieval_report.get(
            "dataset_name"
        )
    )

    final_name = (
        final_report.get(
            "dataset_name"
        )
    )

    retrieval_version = (
        retrieval_report.get(
            "dataset_version"
        )
    )

    final_version = (
        final_report.get(
            "dataset_version"
        )
    )

    if (
        retrieval_name
        != final_name
        or retrieval_version
        != final_version
    ):
        raise ValueError(
            "Retrieval and final RAG "
            "reports must use the same "
            "dataset name and version."
        )


def build_end_to_end_report(
    *,
    retrieval_report: dict[
        str,
        Any,
    ],
    final_report: dict[
        str,
        Any,
    ],
    retrieval_report_path: (
        str | Path | None
    ) = None,
    final_report_path: (
        str | Path | None
    ) = None,
) -> dict[str, Any]:
    _validate_dataset_identity(
        retrieval_report=(
            retrieval_report
        ),
        final_report=(
            final_report
        ),
    )

    results = (
        EndToEndEvaluator
        .evaluate_reports(
            retrieval_report=(
                retrieval_report
            ),
            final_report=(
                final_report
            ),
        )
    )

    summary = (
        aggregate_end_to_end_results(
            results
        )
    )

    return {
        "dataset_name": (
            final_report.get(
                "dataset_name"
            )
        ),
        "dataset_version": (
            final_report.get(
                "dataset_version"
            )
        ),
        "evaluation_mode": (
            "end_to_end_report_composition"
        ),
        "retrieval_report": (
            str(
                retrieval_report_path
            )
            if retrieval_report_path
            is not None
            else None
        ),
        "final_rag_report": (
            str(
                final_report_path
            )
            if final_report_path
            is not None
            else None
        ),
        "summary": summary,
        "cases": [
            asdict(
                result
            )
            for result
            in results
        ],
    }


def main() -> None:
    parser = (
        argparse.ArgumentParser(
            description=(
                "Combine MIRA retrieval "
                "and final RAG reports "
                "into a deterministic "
                "end-to-end evaluation "
                "report."
            )
        )
    )

    parser.add_argument(
        "--retrieval-report",
        required=True,
        help=(
            "Path to a report produced "
            "by live_retrieval_runner."
        ),
    )

    parser.add_argument(
        "--final-report",
        required=True,
        help=(
            "Path to a report produced "
            "by final_rag_runner."
        ),
    )

    parser.add_argument(
        "--report-directory",
        default=str(
            DEFAULT_REPORT_DIRECTORY
        ),
    )

    args = parser.parse_args()

    retrieval_report = (
        _load_json(
            args.retrieval_report
        )
    )

    final_report = (
        _load_json(
            args.final_report
        )
    )

    report = (
        build_end_to_end_report(
            retrieval_report=(
                retrieval_report
            ),
            final_report=(
                final_report
            ),
            retrieval_report_path=(
                args.retrieval_report
            ),
            final_report_path=(
                args.final_report
            ),
        )
    )

    output_path = (
        write_json_report(
            report=report,
            output_directory=(
                args.report_directory
            ),
            prefix=(
                "rag_end_to_end_eval"
            ),
        )
    )

    summary = report[
        "summary"
    ]

    print(
        "MIRA End-to-End "
        "RAG Evaluation"
    )

    print(
        "=============================="
    )

    print(
        "Dataset: "
        f"{report['dataset_name']} "
        f"{report['dataset_version']}"
    )

    print(
        "Cases: "
        f"{summary['case_count']}"
    )

    print(
        "Successes: "
        f"{summary['success_count']}"
    )

    print(
        "Success Rate: "
        f"{summary['success_rate']:.3f}"
    )

    failure_counts = (
        summary[
            "failure_counts"
        ]
    )

    if failure_counts:
        print(
            "Failure Reasons:"
        )

        for (
            reason,
            count,
        ) in failure_counts.items():
            print(
                f"  {reason}: "
                f"{count}"
            )

    else:
        print(
            "Failure Reasons: none"
        )

    print(
        "By Task:"
    )

    for (
        task,
        values,
    ) in summary[
        "by_task"
    ].items():
        print(
            f"  {task}: "
            f"{values['success_count']}/"
            f"{values['case_count']} "
            f"("
            f"{values['success_rate']:.3f}"
            f")"
        )

    print(
        f"Report: {output_path}"
    )


if __name__ == "__main__":
    main()
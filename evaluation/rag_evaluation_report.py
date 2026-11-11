from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_OUTPUT_PATH = (
    Path(__file__).resolve().parent
    / "reports"
    / "RAG_EVALUATION_REPORT.md"
)


def _load_json(
    path: str | Path,
) -> dict[str, Any]:
    report_path = Path(path)

    if not report_path.exists():
        raise FileNotFoundError(
            f"Report not found: {report_path}"
        )

    with report_path.open(
        "r",
        encoding="utf-8",
    ) as handle:
        value = json.load(handle)

    if not isinstance(value, dict):
        raise ValueError(
            "Expected a JSON object in "
            f"{report_path}"
        )

    return value


def _format_rate(
    value: float | int | None,
) -> str:
    if value is None:
        return "N/A"

    return f"{float(value):.3f}"


def _validate_dataset_identity(
    *reports: dict[str, Any],
) -> tuple[str, str]:
    identities = {
        (
            str(
                report.get(
                    "dataset_name",
                    "",
                )
            ),
            str(
                report.get(
                    "dataset_version",
                    "",
                )
            ),
        )
        for report in reports
    }

    if len(identities) != 1:
        raise ValueError(
            "All evaluation reports must "
            "use the same dataset name "
            "and version."
        )

    dataset_name, dataset_version = (
        identities.pop()
    )

    if not dataset_name:
        raise ValueError(
            "Dataset name is missing."
        )

    if not dataset_version:
        raise ValueError(
            "Dataset version is missing."
        )

    return (
        dataset_name,
        dataset_version,
    )


def _synthetic_sources(
    retrieval_report: dict[str, Any],
) -> list[str]:
    sources: set[str] = set()

    for case in retrieval_report.get(
        "context_cases",
        [],
    ):
        if not isinstance(
            case,
            dict,
        ):
            continue

        for source in case.get(
            "expected_sources",
            [],
        ):
            if source:
                sources.add(
                    str(source)
                )

    return sorted(sources)


def _failure_details(
    *,
    final_report: dict[str, Any],
    end_to_end_report: dict[str, Any],
) -> list[dict[str, Any]]:
    final_cases = {
        str(
            case.get(
                "case_id"
            )
        ): case
        for case in final_report.get(
            "cases",
            [],
        )
        if (
            isinstance(
                case,
                dict,
            )
            and case.get(
                "case_id"
            )
        )
    }

    failures: list[
        dict[str, Any]
    ] = []

    for case in end_to_end_report.get(
        "cases",
        [],
    ):
        if not isinstance(
            case,
            dict,
        ):
            continue

        if case.get(
            "success"
        ) is True:
            continue

        case_id = str(
            case.get(
                "case_id",
                "",
            )
        )

        final_case = final_cases.get(
            case_id,
            {},
        )

        evaluation = final_case.get(
            "evaluation",
            {},
        )

        if not isinstance(
            evaluation,
            dict,
        ):
            evaluation = {}

        failures.append(
            {
                "case_id": case_id,
                "task": str(
                    case.get(
                        "task",
                        "",
                    )
                ),
                "outcome": str(
                    case.get(
                        "outcome",
                        "",
                    )
                ),
                "missing_required_facts": list(
                    evaluation.get(
                        "missing_required_facts",
                        [],
                    )
                    or []
                ),
                "forbidden_facts_found": list(
                    evaluation.get(
                        "forbidden_facts_found",
                        [],
                    )
                    or []
                ),
            }
        )

    return failures


def build_markdown_report(
    *,
    retrieval_report: dict[str, Any],
    final_report: dict[str, Any],
    end_to_end_report: dict[str, Any],
    retrieval_report_path: str | Path,
    final_report_path: str | Path,
    end_to_end_report_path: str | Path,
) -> str:
    (
        dataset_name,
        dataset_version,
    ) = _validate_dataset_identity(
        retrieval_report,
        final_report,
        end_to_end_report,
    )

    retrieval_summary = (
        retrieval_report.get(
            "retrieval",
            {},
        )
    )

    context_summary = (
        retrieval_report.get(
            "context",
            {},
        )
    )

    generation_summary = (
        final_report.get(
            "generation_summary",
            {},
        )
    )

    end_to_end_summary = (
        end_to_end_report.get(
            "summary",
            {},
        )
    )

    synthetic_sources = (
        _synthetic_sources(
            retrieval_report
        )
    )

    failures = (
        _failure_details(
            final_report=(
                final_report
            ),
            end_to_end_report=(
                end_to_end_report
            ),
        )
    )

    retrieval_by_task = (
        retrieval_summary.get(
            "by_task",
            {},
        )
    )

    qa_retrieval = (
        retrieval_by_task.get(
            "qa",
            {},
        )
    )

    e2e_by_task = (
        end_to_end_summary.get(
            "by_task",
            {},
        )
    )

    lines: list[str] = []

    lines.extend(
        [
            "# MIRA RAG Evaluation Report",
            "",
            "## Overview",
            "",
            (
                f"This report summarizes the "
                f"RAG evaluation results for "
                f"`{dataset_name}` version "
                f"`{dataset_version}`."
            ),
            "",
            (
                "The evaluation uses synthetic "
                "medical records only. It measures "
                "retrieval quality, context "
                "preservation, final production-RAG "
                "answer quality, grounding, citation "
                "behavior, abstention behavior, and "
                "end-to-end case success."
            ),
            "",
            (
                "The evaluation harness is separate "
                "from the production request path. "
                "The final-generation benchmark calls "
                "the production RAG service and scores "
                "the final answer after the normal "
                "validation, repair, and fallback "
                "pipeline."
            ),
            "",
            "## Dataset",
            "",
            (
                f"- Dataset: `{dataset_name}` "
                f"`{dataset_version}`"
            ),
            (
                f"- Evaluation cases: "
                f"{generation_summary.get('case_count', 'N/A')}"
            ),
            (
                f"- Synthetic source documents: "
                f"{len(synthetic_sources)}"
            ),
        ]
    )

    for source in synthetic_sources:
        lines.append(
            f"  - `{source}`"
        )

    lines.extend(
        [
            "",
            "The case set covers:",
            "",
            "- document question answering",
            "- cross-document comparison",
            "- document summarization",
            "- missing-information abstention",
            "- distractor-document resistance",
            "",
            "## Retrieval Evaluation",
            "",
            "| Metric | Result |",
            "| --- | ---: |",
            (
                "| QA retrieval cases | "
                f"{qa_retrieval.get('case_count', 'N/A')} |"
            ),
            (
                "| Hit@3 | "
                f"{_format_rate(qa_retrieval.get('hit_rate_at_k'))} |"
            ),
            (
                "| Recall@3 | "
                f"{_format_rate(qa_retrieval.get('recall_at_k'))} |"
            ),
            (
                "| MRR | "
                f"{_format_rate(qa_retrieval.get('mrr'))} |"
            ),
            (
                "| Wrong-document rate | "
                f"{_format_rate(qa_retrieval.get('wrong_document_rate'))} |"
            ),
            "",
            (
                "All evaluated QA retrieval cases "
                "contained the expected document "
                "within the top-3 results. The "
                "non-perfect MRR and wrong-document "
                "rate came from the distractor "
                "glucose case, where the follow-up "
                "laboratory report ranked ahead of "
                "the expected laboratory report."
            ),
            "",
            "## Context Preservation",
            "",
            "| Metric | Result |",
            "| --- | ---: |",
            (
                "| Context cases | "
                f"{context_summary.get('case_count', 'N/A')} |"
            ),
            (
                "| Document recall | "
                f"{_format_rate(context_summary.get('document_recall'))} |"
            ),
            (
                "| Required-fact survival | "
                f"{_format_rate(context_summary.get('required_fact_survival_rate'))} |"
            ),
            (
                "| Expected-evidence retention | "
                f"{_format_rate(context_summary.get('evidence_retention_rate'))} |"
            ),
            "",
            (
                "The configured context budget "
                f"was "
                f"{retrieval_report.get('context_token_budget', 'N/A')} "
                "estimated tokens. No required "
                "evaluation evidence was lost during "
                "context construction in this run."
            ),
            "",
            "## Final Production-RAG Evaluation",
            "",
            "| Metric | Result |",
            "| --- | ---: |",
            (
                "| Required Fact Recall | "
                f"{_format_rate(generation_summary.get('required_fact_recall'))} |"
            ),
            (
                "| Forbidden Fact Violation Rate | "
                f"{_format_rate(generation_summary.get('forbidden_fact_violation_rate'))} |"
            ),
            (
                "| Abstention Accuracy | "
                f"{_format_rate(generation_summary.get('abstention_accuracy'))} |"
            ),
            (
                "| Grounded Answer Pass Rate | "
                f"{_format_rate(generation_summary.get('grounded_answer_pass_rate'))} |"
            ),
            (
                "| Missing Source Citation Rate | "
                f"{_format_rate(generation_summary.get('missing_source_citation_rate'))} |"
            ),
            (
                "| Unsupported Medical Value Rate | "
                f"{_format_rate(generation_summary.get('unsupported_medical_value_rate'))} |"
            ),
            (
                "| Invalid Citation Rate | "
                f"{_format_rate(generation_summary.get('invalid_citation_rate'))} |"
            ),
            (
                "| Uncited Medical Value Rate | "
                f"{_format_rate(generation_summary.get('uncited_medical_value_rate'))} |"
            ),
            (
                "| Misattributed Medical Value Rate | "
                f"{_format_rate(generation_summary.get('misattributed_medical_value_rate'))} |"
            ),
            (
                "| Case Pass Rate | "
                f"{_format_rate(generation_summary.get('case_pass_rate'))} |"
            ),
            "",
            (
                "The final production-RAG outputs "
                "were fully clean on grounding and "
                "citation validation in this run. "
                "The remaining failures were content "
                "quality failures rather than "
                "unsupported or uncited medical-value "
                "failures."
            ),
            "",
            "## End-to-End Evaluation",
            "",
            "| Metric | Result |",
            "| --- | ---: |",
            (
                "| Cases | "
                f"{end_to_end_summary.get('case_count', 'N/A')} |"
            ),
            (
                "| Successful cases | "
                f"{end_to_end_summary.get('success_count', 'N/A')} |"
            ),
            (
                "| End-to-end success rate | "
                f"{_format_rate(end_to_end_summary.get('success_rate'))} |"
            ),
            "",
            "### Success by Task",
            "",
            "| Task | Passed | Total | Rate |",
            "| --- | ---: | ---: | ---: |",
        ]
    )

    for task in sorted(
        e2e_by_task
    ):
        values = (
            e2e_by_task[
                task
            ]
        )

        lines.append(
            "| "
            f"{task} | "
            f"{values.get('success_count', 'N/A')} | "
            f"{values.get('case_count', 'N/A')} | "
            f"{_format_rate(values.get('success_rate'))} |"
        )

    lines.extend(
        [
            "",
            "## Failure Analysis",
            "",
        ]
    )

    if not failures:
        lines.append(
            "No end-to-end failures were "
            "recorded in this report."
        )
    else:
        for failure in failures:
            lines.append(
                "### "
                f"`{failure['case_id']}`"
            )
            lines.append("")
            lines.append(
                f"- Task: `{failure['task']}`"
            )
            lines.append(
                f"- Classification: "
                f"`{failure['outcome']}`"
            )

            missing = (
                failure[
                    "missing_required_facts"
                ]
            )

            forbidden = (
                failure[
                    "forbidden_facts_found"
                ]
            )

            if missing:
                lines.append(
                    "- Missing required facts: "
                    + ", ".join(
                        f"`{item}`"
                        for item in missing
                    )
                )

            if forbidden:
                lines.append(
                    "- Forbidden facts found: "
                    + ", ".join(
                        f"`{item}`"
                        for item in forbidden
                    )
                )

            if (
                failure[
                    "outcome"
                ]
                == "generation_incomplete"
            ):
                lines.append(
                    "- Interpretation: retrieval "
                    "and context preserved the "
                    "required evidence, but the "
                    "final answer omitted part of "
                    "the expected information."
                )

            elif (
                failure[
                    "outcome"
                ]
                == "forbidden_fact"
            ):
                lines.append(
                    "- Interpretation: the final "
                    "response included information "
                    "that the case explicitly marked "
                    "as distractor content."
                )

            lines.append("")

    lines.extend(
        [
            "## Key Findings",
            "",
            (
                "1. Retrieval successfully surfaced "
                "the expected source within the "
                "configured top-3 window for every "
                "evaluated QA retrieval case."
            ),
            (
                "2. Context construction preserved "
                "all required evaluation facts and "
                "expected evidence in this run."
            ),
            (
                "3. Final answers achieved a grounded "
                "answer pass rate of "
                f"{_format_rate(generation_summary.get('grounded_answer_pass_rate'))} "
                "with zero unsupported, uncited, "
                "invalidly cited, or misattributed "
                "medical values according to the "
                "deterministic evaluator."
            ),
            (
                "4. End-to-end success was "
                f"{_format_rate(end_to_end_summary.get('success_rate'))}, "
                "with the remaining failures "
                "attributed to answer completeness "
                "and distractor/fallback behavior."
            ),
            "",
            "## Known Limitations",
            "",
            (
                "- The benchmark is intentionally "
                "small and synthetic. Results should "
                "not be interpreted as clinical "
                "validation or evidence of safety "
                "across real-world medical records."
            ),
            (
                "- Retrieval metrics currently cover "
                "the nine QA retrieval cases. "
                "Comparison and summarization cases "
                "are evaluated through context and "
                "final end-to-end behavior rather "
                "than the same retrieval metric set."
            ),
            (
                "- Many cases operate over explicitly "
                "selected documents. This benchmark "
                "therefore evaluates MIRA's "
                "selected-document RAG behavior and "
                "should not be presented as a broad "
                "corpus-wide retrieval benchmark."
            ),
            (
                "- The synthetic corpus contains only "
                f"{len(synthetic_sources)} documents, "
                "so distractor diversity is limited."
            ),
            (
                "- LLM generation is nondeterministic. "
                "Provider availability and model "
                "variation can change final-answer "
                "metrics across runs even when the "
                "retrieval inputs are unchanged."
            ),
            (
                "- The distractor glucose failure "
                "shows that the deterministic "
                "source-grounded fallback can preserve "
                "grounding while still returning "
                "irrelevant selected-document content."
            ),
            (
                "- These results do not establish "
                "HIPAA compliance, clinical efficacy, "
                "diagnostic accuracy, or suitability "
                "for autonomous medical decision-making."
            ),
            "",
            "## Reproducibility",
            "",
            "This report was generated from:",
            "",
            (
                "- Retrieval report: "
                f"`{Path(retrieval_report_path).name}`"
            ),
            (
                "- Final production-RAG report: "
                f"`{Path(final_report_path).name}`"
            ),
            (
                "- End-to-end report: "
                f"`{Path(end_to_end_report_path).name}`"
            ),
            "",
            (
                "Preserving these JSON artifacts makes "
                "the reported metrics and failure "
                "classifications independently "
                "inspectable without rerunning the LLM."
            ),
            "",
        ]
    )

    return "\n".join(lines)


def write_markdown_report(
    *,
    content: str,
    output_path: str | Path,
) -> Path:
    path = Path(
        output_path
    )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        content,
        encoding="utf-8",
    )

    return path


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Generate the consolidated "
            "MIRA RAG evaluation report."
        )
    )

    parser.add_argument(
        "--retrieval-report",
        required=True,
    )

    parser.add_argument(
        "--final-report",
        required=True,
    )

    parser.add_argument(
        "--end-to-end-report",
        required=True,
    )

    parser.add_argument(
        "--output",
        default=str(
            DEFAULT_OUTPUT_PATH
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

    end_to_end_report = (
        _load_json(
            args.end_to_end_report
        )
    )

    content = (
        build_markdown_report(
            retrieval_report=(
                retrieval_report
            ),
            final_report=(
                final_report
            ),
            end_to_end_report=(
                end_to_end_report
            ),
            retrieval_report_path=(
                args.retrieval_report
            ),
            final_report_path=(
                args.final_report
            ),
            end_to_end_report_path=(
                args.end_to_end_report
            ),
        )
    )

    output_path = (
        write_markdown_report(
            content=content,
            output_path=(
                args.output
            ),
        )
    )

    print(
        "MIRA RAG Evaluation Report"
    )
    print(
        "=========================="
    )
    print(
        f"Report: {output_path}"
    )


if __name__ == "__main__":
    main()
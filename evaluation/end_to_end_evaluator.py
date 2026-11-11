from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any


SUCCESS = "success"
EXECUTION_FAILURE = "execution_failure"
RETRIEVAL_FAILURE = "retrieval_failure"
CONTEXT_LOSS = "context_loss"
GROUNDING_FAILURE = "grounding_failure"
ABSTENTION_FAILURE = "abstention_failure"
FORBIDDEN_FACT = "forbidden_fact"
GENERATION_INCOMPLETE = "generation_incomplete"


@dataclass(frozen=True)
class EndToEndCaseResult:
    case_id: str
    task: str
    outcome: str
    success: bool

    retrieval_hit: bool | None
    retrieval_recall: float | None
    reciprocal_rank: float | None
    wrong_document_rate: float | None

    context_document_recall: float | None
    required_fact_survival_rate: float | None
    expected_evidence_retained: bool | None

    required_fact_recall: float | None
    forbidden_fact_violation: bool | None
    abstention_correct: bool | None
    grounding_valid: bool | None


class EndToEndEvaluator:
    """
    Combines retrieval, optimized-context, and final-generation
    evaluation results into one deterministic end-to-end outcome.

    Failure classification is intentionally ordered from earliest
    pipeline stage to latest pipeline stage so downstream failures
    do not hide an upstream retrieval or context failure.
    """

    @staticmethod
    def evaluate_case(
        *,
        retrieval_case: dict[str, Any] | None,
        context_case: dict[str, Any] | None,
        final_case: dict[str, Any],
    ) -> EndToEndCaseResult:
        case_id = str(
            final_case.get(
                "case_id",
                "",
            )
        ).strip()

        task = str(
            final_case.get(
                "task",
                "",
            )
        ).strip()

        execution_status = str(
            final_case.get(
                "execution_status",
                "completed",
            )
        ).strip().casefold()

        evaluation = final_case.get(
            "evaluation",
            {},
        )

        if not isinstance(
            evaluation,
            dict,
        ):
            evaluation = {}

        grounding = final_case.get(
            "grounding",
            {},
        )

        if not isinstance(
            grounding,
            dict,
        ):
            grounding = {}

        retrieval_hit = (
            bool(
                retrieval_case.get(
                    "hit_at_k"
                )
            )
            if (
                retrieval_case
                and "hit_at_k"
                in retrieval_case
            )
            else None
        )

        retrieval_recall = (
            float(
                retrieval_case[
                    "recall_at_k"
                ]
            )
            if (
                retrieval_case
                and retrieval_case.get(
                    "recall_at_k"
                )
                is not None
            )
            else None
        )

        reciprocal_rank = (
            float(
                retrieval_case[
                    "reciprocal_rank"
                ]
            )
            if (
                retrieval_case
                and retrieval_case.get(
                    "reciprocal_rank"
                )
                is not None
            )
            else None
        )

        wrong_document_rate = (
            float(
                retrieval_case[
                    "wrong_document_rate"
                ]
            )
            if (
                retrieval_case
                and retrieval_case.get(
                    "wrong_document_rate"
                )
                is not None
            )
            else None
        )

        context_document_recall = (
            float(
                context_case[
                    "document_recall"
                ]
            )
            if (
                context_case
                and context_case.get(
                    "document_recall"
                )
                is not None
            )
            else None
        )

        required_fact_survival_rate = (
            float(
                context_case[
                    "required_fact_survival_rate"
                ]
            )
            if (
                context_case
                and context_case.get(
                    "required_fact_survival_rate"
                )
                is not None
            )
            else None
        )

        expected_evidence_retained = (
            bool(
                context_case.get(
                    "expected_evidence_retained"
                )
            )
            if (
                context_case
                and "expected_evidence_retained"
                in context_case
            )
            else None
        )

        required_fact_recall = (
            float(
                evaluation[
                    "required_fact_recall"
                ]
            )
            if (
                evaluation.get(
                    "required_fact_recall"
                )
                is not None
            )
            else None
        )

        forbidden_fact_violation = (
            bool(
                evaluation.get(
                    "forbidden_fact_violation"
                )
            )
            if (
                "forbidden_fact_violation"
                in evaluation
            )
            else None
        )

        abstention_correct = (
            bool(
                evaluation.get(
                    "abstention_correct"
                )
            )
            if (
                "abstention_correct"
                in evaluation
            )
            else None
        )

        grounding_valid = (
            bool(
                grounding.get(
                    "is_valid"
                )
            )
            if (
                "is_valid"
                in grounding
            )
            else None
        )

        if execution_status not in {
            "",
            "completed",
            "success",
            "ok",
        }:
            outcome = (
                EXECUTION_FAILURE
            )

        elif (
            retrieval_case
            is not None
            and (
                retrieval_hit is False
                or (
                    retrieval_recall
                    is not None
                    and retrieval_recall
                    < 1.0
                )
            )
        ):
            outcome = (
                RETRIEVAL_FAILURE
            )

        elif (
            context_case
            is not None
            and (
                expected_evidence_retained
                is False
                or (
                    context_document_recall
                    is not None
                    and context_document_recall
                    < 1.0
                )
                or (
                    required_fact_survival_rate
                    is not None
                    and required_fact_survival_rate
                    < 1.0
                )
            )
        ):
            outcome = CONTEXT_LOSS

        elif grounding_valid is False:
            outcome = (
                GROUNDING_FAILURE
            )

        elif abstention_correct is False:
            outcome = (
                ABSTENTION_FAILURE
            )

        elif (
            forbidden_fact_violation
            is True
        ):
            outcome = FORBIDDEN_FACT

        elif (
            required_fact_recall
            is not None
            and required_fact_recall
            < 1.0
        ):
            outcome = (
                GENERATION_INCOMPLETE
            )

        else:
            outcome = SUCCESS

        return EndToEndCaseResult(
            case_id=case_id,
            task=task,
            outcome=outcome,
            success=(
                outcome == SUCCESS
            ),
            retrieval_hit=(
                retrieval_hit
            ),
            retrieval_recall=(
                retrieval_recall
            ),
            reciprocal_rank=(
                reciprocal_rank
            ),
            wrong_document_rate=(
                wrong_document_rate
            ),
            context_document_recall=(
                context_document_recall
            ),
            required_fact_survival_rate=(
                required_fact_survival_rate
            ),
            expected_evidence_retained=(
                expected_evidence_retained
            ),
            required_fact_recall=(
                required_fact_recall
            ),
            forbidden_fact_violation=(
                forbidden_fact_violation
            ),
            abstention_correct=(
                abstention_correct
            ),
            grounding_valid=(
                grounding_valid
            ),
        )

    @classmethod
    def evaluate_reports(
        cls,
        *,
        retrieval_report: dict[
            str,
            Any,
        ],
        final_report: dict[
            str,
            Any,
        ],
    ) -> list[
        EndToEndCaseResult
    ]:
        retrieval_map = {
            str(
                item["case_id"]
            ): item
            for item
            in retrieval_report.get(
                "retrieval_cases",
                [],
            )
            if (
                isinstance(
                    item,
                    dict,
                )
                and item.get(
                    "case_id"
                )
            )
        }

        context_map = {
            str(
                item["case_id"]
            ): item
            for item
            in retrieval_report.get(
                "context_cases",
                [],
            )
            if (
                isinstance(
                    item,
                    dict,
                )
                and item.get(
                    "case_id"
                )
            )
        }

        results: list[
            EndToEndCaseResult
        ] = []

        for final_case in (
            final_report.get(
                "cases",
                [],
            )
        ):
            if (
                not isinstance(
                    final_case,
                    dict,
                )
                or not final_case.get(
                    "case_id"
                )
            ):
                continue

            case_id = str(
                final_case[
                    "case_id"
                ]
            )

            results.append(
                cls.evaluate_case(
                    retrieval_case=(
                        retrieval_map.get(
                            case_id
                        )
                    ),
                    context_case=(
                        context_map.get(
                            case_id
                        )
                    ),
                    final_case=(
                        final_case
                    ),
                )
            )

        return results


def aggregate_end_to_end_results(
    results: list[
        EndToEndCaseResult
    ],
) -> dict[str, Any]:
    if not results:
        return {
            "case_count": 0,
            "success_count": 0,
            "success_rate": 0.0,
            "failure_counts": {},
            "by_task": {},
        }

    success_count = sum(
        result.success
        for result in results
    )

    failure_counts = Counter(
        result.outcome
        for result in results
        if not result.success
    )

    by_task: dict[
        str,
        dict[str, Any],
    ] = {}

    tasks = sorted(
        {
            result.task
            for result in results
        }
    )

    for task in tasks:
        task_results = [
            result
            for result in results
            if result.task == task
        ]

        task_successes = sum(
            result.success
            for result
            in task_results
        )

        task_failures = Counter(
            result.outcome
            for result
            in task_results
            if not result.success
        )

        by_task[
            task
        ] = {
            "case_count": len(
                task_results
            ),
            "success_count": (
                task_successes
            ),
            "success_rate": (
                task_successes
                / len(
                    task_results
                )
                if task_results
                else 0.0
            ),
            "failure_counts": dict(
                sorted(
                    task_failures.items()
                )
            ),
        }

    return {
        "case_count": len(
            results
        ),
        "success_count": (
            success_count
        ),
        "success_rate": (
            success_count
            / len(
                results
            )
        ),
        "failure_counts": dict(
            sorted(
                failure_counts.items()
            )
        ),
        "by_task": by_task,
    }
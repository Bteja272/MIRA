from evaluation.end_to_end_evaluator import (
    CONTEXT_LOSS,
    FORBIDDEN_FACT,
    GENERATION_INCOMPLETE,
    RETRIEVAL_FAILURE,
    SUCCESS,
    EndToEndEvaluator,
    aggregate_end_to_end_results,
)


def _final_case(
    *,
    case_id="case-1",
    task="qa",
    required_fact_recall=1.0,
    forbidden=False,
    abstention=True,
    grounding=True,
):
    return {
        "case_id": case_id,
        "task": task,
        "grounding": {
            "is_valid": (
                grounding
            ),
        },
        "evaluation": {
            "required_fact_recall": (
                required_fact_recall
            ),
            "forbidden_fact_violation": (
                forbidden
            ),
            "abstention_correct": (
                abstention
            ),
        },
    }


def _retrieval_case(
    *,
    hit=True,
    recall=1.0,
):
    return {
        "case_id": "case-1",
        "hit_at_k": hit,
        "recall_at_k": recall,
        "reciprocal_rank": 1.0,
        "wrong_document_rate": 0.0,
    }


def _context_case(
    *,
    retained=True,
    document_recall=1.0,
    fact_survival=1.0,
):
    return {
        "case_id": "case-1",
        "document_recall": (
            document_recall
        ),
        "required_fact_survival_rate": (
            fact_survival
        ),
        "expected_evidence_retained": (
            retained
        ),
    }


def test_success_case():
    result = (
        EndToEndEvaluator
        .evaluate_case(
            retrieval_case=(
                _retrieval_case()
            ),
            context_case=(
                _context_case()
            ),
            final_case=(
                _final_case()
            ),
        )
    )

    assert (
        result.outcome
        == SUCCESS
    )

    assert (
        result.success
        is True
    )


def test_retrieval_failure_has_priority():
    result = (
        EndToEndEvaluator
        .evaluate_case(
            retrieval_case=(
                _retrieval_case(
                    hit=False,
                    recall=0.0,
                )
            ),
            context_case=(
                _context_case(
                    retained=False,
                )
            ),
            final_case=(
                _final_case(
                    required_fact_recall=0.0,
                )
            ),
        )
    )

    assert (
        result.outcome
        == RETRIEVAL_FAILURE
    )


def test_context_loss():
    result = (
        EndToEndEvaluator
        .evaluate_case(
            retrieval_case=(
                _retrieval_case()
            ),
            context_case=(
                _context_case(
                    fact_survival=0.5,
                    retained=False,
                )
            ),
            final_case=(
                _final_case()
            ),
        )
    )

    assert (
        result.outcome
        == CONTEXT_LOSS
    )


def test_forbidden_fact():
    result = (
        EndToEndEvaluator
        .evaluate_case(
            retrieval_case=(
                _retrieval_case()
            ),
            context_case=(
                _context_case()
            ),
            final_case=(
                _final_case(
                    forbidden=True,
                )
            ),
        )
    )

    assert (
        result.outcome
        == FORBIDDEN_FACT
    )


def test_generation_incomplete():
    result = (
        EndToEndEvaluator
        .evaluate_case(
            retrieval_case=(
                _retrieval_case()
            ),
            context_case=(
                _context_case()
            ),
            final_case=(
                _final_case(
                    required_fact_recall=0.5,
                )
            ),
        )
    )

    assert (
        result.outcome
        == GENERATION_INCOMPLETE
    )


def test_aggregate_results():
    success = (
        EndToEndEvaluator
        .evaluate_case(
            retrieval_case=(
                _retrieval_case()
            ),
            context_case=(
                _context_case()
            ),
            final_case=(
                _final_case(
                    case_id="ok",
                )
            ),
        )
    )

    failure = (
        EndToEndEvaluator
        .evaluate_case(
            retrieval_case=(
                _retrieval_case()
            ),
            context_case=(
                _context_case()
            ),
            final_case=(
                _final_case(
                    case_id="bad",
                    required_fact_recall=0.5,
                )
            ),
        )
    )

    summary = (
        aggregate_end_to_end_results(
            [
                success,
                failure,
            ]
        )
    )

    assert (
        summary[
            "case_count"
        ]
        == 2
    )

    assert (
        summary[
            "success_count"
        ]
        == 1
    )

    assert (
        summary[
            "success_rate"
        ]
        == 0.5
    )

    assert (
        summary[
            "failure_counts"
        ][
            GENERATION_INCOMPLETE
        ]
        == 1
    )
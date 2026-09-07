from evaluation.generation_evaluator import (
    GenerationEvaluator,
    aggregate_generation_results,
)
from evaluation.models import RAGEvalCase


def _case(
    *,
    expected_abstention=False,
    required_facts=("11.2 g/dL",),
    forbidden_facts=(),
):
    return RAGEvalCase(
        case_id="case-1",
        task="qa",
        query="Synthetic query",
        documents=("lab.txt",),
        expected_documents=("lab.txt",),
        required_facts=tuple(
            required_facts
        ),
        forbidden_facts=tuple(
            forbidden_facts
        ),
        expected_abstention=(
            expected_abstention
        ),
    )


def test_generation_passes_when_expected_fact_present():
    result = (
        GenerationEvaluator.evaluate(
            case=_case(),
            answer=(
                "The result was "
                "11.2 g/dL [Source 1]."
            ),
            grounded_is_valid=True,
        )
    )

    assert (
        result.required_fact_recall
        == 1.0
    )
    assert (
        result.forbidden_fact_violation
        is False
    )
    assert result.case_passed is True


def test_generation_detects_missing_required_fact():
    result = (
        GenerationEvaluator.evaluate(
            case=_case(),
            answer=(
                "The result is documented "
                "[Source 1]."
            ),
            grounded_is_valid=True,
        )
    )

    assert (
        result.required_fact_recall
        == 0.0
    )
    assert (
        result.missing_required_facts
        == ("11.2 g/dL",)
    )
    assert result.case_passed is False


def test_generation_detects_forbidden_fact():
    result = (
        GenerationEvaluator.evaluate(
            case=_case(
                forbidden_facts=(
                    "96 mg/dL",
                )
            ),
            answer=(
                "The result was "
                "11.2 g/dL [Source 1]. "
                "Another value was "
                "96 mg/dL [Source 1]."
            ),
            grounded_is_valid=True,
        )
    )

    assert (
        result.forbidden_fact_violation
        is True
    )
    assert (
        result.forbidden_facts_found
        == ("96 mg/dL",)
    )
    assert result.case_passed is False


def test_expected_abstention_is_detected():
    result = (
        GenerationEvaluator.evaluate(
            case=_case(
                expected_abstention=True,
                required_facts=(),
            ),
            answer=(
                "The blood type is not "
                "documented in the supplied "
                "context [Source 1]."
            ),
            grounded_is_valid=True,
        )
    )

    assert (
        result.abstention_correct
        is True
    )
    assert result.case_passed is True


def test_unexpected_abstention_fails():
    result = (
        GenerationEvaluator.evaluate(
            case=_case(),
            answer=(
                "The result is not "
                "documented."
            ),
            grounded_is_valid=True,
        )
    )

    assert (
        result.abstention_correct
        is False
    )
    assert result.case_passed is False


def test_grounding_failure_fails_case():
    result = (
        GenerationEvaluator.evaluate(
            case=_case(),
            answer=(
                "The result was "
                "11.2 g/dL."
            ),
            grounded_is_valid=False,
        )
    )

    assert result.case_passed is False


def test_aggregate_generation_results():
    passing = (
        GenerationEvaluator.evaluate(
            case=_case(),
            answer=(
                "11.2 g/dL [Source 1]."
            ),
            grounded_is_valid=True,
        )
    )

    failing = (
        GenerationEvaluator.evaluate(
            case=_case(
                forbidden_facts=(
                    "96 mg/dL",
                )
            ),
            answer=(
                "96 mg/dL [Source 1]."
            ),
            grounded_is_valid=False,
        )
    )

    summary = (
        aggregate_generation_results(
            [
                passing,
                failing,
            ]
        )
    )

    assert summary["case_count"] == 2
    assert (
        summary["required_fact_recall"]
        == 0.5
    )
    assert (
        summary[
            "forbidden_fact_violation_rate"
        ]
        == 0.5
    )
    assert (
        summary["case_pass_rate"]
        == 0.5
    )

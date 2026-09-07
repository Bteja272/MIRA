from evaluation.generation_evaluator import (
    GenerationEvaluator,
)
from evaluation.models import (
    RAGEvalCase,
)


def _case(
    *,
    expected_abstention=False,
    forbidden_facts=(),
):
    return RAGEvalCase(
        case_id="case-1",
        task="qa",
        query="Synthetic query",
        documents=("one.txt",),
        expected_documents=("one.txt",),
        required_facts=(),
        forbidden_facts=tuple(
            forbidden_facts
        ),
        expected_abstention=(
            expected_abstention
        ),
    )


def test_negated_forbidden_phrase_is_not_violation():
    result = (
        GenerationEvaluator.evaluate(
            case=_case(
                forbidden_facts=(
                    "antibiotics were prescribed",
                )
            ),
            answer=(
                "No antibiotics were prescribed "
                "at discharge. [Source 1]"
            ),
            grounded_is_valid=True,
        )
    )

    assert (
        result.forbidden_fact_violation
        is False
    )
    assert (
        result.forbidden_facts_found
        == ()
    )


def test_affirmative_forbidden_phrase_is_violation():
    result = (
        GenerationEvaluator.evaluate(
            case=_case(
                forbidden_facts=(
                    "antibiotics were prescribed",
                )
            ),
            answer=(
                "Antibiotics were prescribed "
                "at discharge. [Source 1]"
            ),
            grounded_is_valid=True,
        )
    )

    assert (
        result.forbidden_fact_violation
        is True
    )


def test_does_not_document_is_abstention():
    result = (
        GenerationEvaluator.evaluate(
            case=_case(
                expected_abstention=True
            ),
            answer=(
                "The supplied medication list "
                "does not document any "
                "medication allergy. [Source 1]"
            ),
            grounded_is_valid=True,
        )
    )

    assert (
        result.abstention_correct
        is True
    )


def test_unrelated_forbidden_value_still_fails():
    result = (
        GenerationEvaluator.evaluate(
            case=_case(
                forbidden_facts=(
                    "96 mg/dL",
                )
            ),
            answer=(
                "January glucose was "
                "108 mg/dL [Source 1]. "
                "The source text also contains "
                "96 mg/dL [Source 2]."
            ),
            grounded_is_valid=True,
        )
    )

    assert (
        result.forbidden_fact_violation
        is True
    )

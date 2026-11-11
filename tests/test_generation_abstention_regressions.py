from evaluation.generation_evaluator import (
    GenerationEvaluator,
)
from evaluation.models import (
    RAGEvalCase,
)


def _case():
    return RAGEvalCase(
        case_id="case-1",
        task="qa",
        query="Synthetic query",
        documents=("one.txt",),
        expected_documents=("one.txt",),
        required_facts=(),
        forbidden_facts=(),
        expected_abstention=True,
    )


def test_not_reported_is_abstention():
    result = (
        GenerationEvaluator.evaluate(
            case=_case(),
            answer=(
                "The blood type is not reported "
                "in the supplied document. "
                "[Source 1]"
            ),
            grounded_is_valid=True,
        )
    )

    assert (
        result.abstention_correct
        is True
    )
    assert result.case_passed is True


def test_no_medication_allergy_is_documented():
    result = (
        GenerationEvaluator.evaluate(
            case=_case(),
            answer=(
                "No medication allergy is "
                "documented in the supplied "
                "medication list. [Source 1]"
            ),
            grounded_is_valid=True,
        )
    )

    assert (
        result.abstention_correct
        is True
    )
    assert result.case_passed is True


def test_no_reference_to_allergies_is_abstention():
    result = (
        GenerationEvaluator.evaluate(
            case=_case(),
            answer=(
                "There is no reference to any "
                "allergies in the source. "
                "[Source 1]"
            ),
            grounded_is_valid=True,
        )
    )

    assert (
        result.abstention_correct
        is True
    )

def test_does_not_include_any_information_is_abstention():
    result = (
        GenerationEvaluator.evaluate(
            case=_case(),
            answer=(
                "The supplied laboratory report "
                "does not include any information "
                "about the patient's blood type. "
                "[Source 1]"
            ),
            grounded_is_valid=True,
        )
    )

    assert result.abstention_correct is True
    assert result.case_passed is True
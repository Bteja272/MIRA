from evaluation.final_rag_runner import (
    FinalRAGRunner,
)
from evaluation.generation_evaluator import (
    GenerationEvaluator,
)
from evaluation.models import (
    RAGEvalCase,
)


def _case(
    *,
    expected_abstention=False,
    required_facts=(),
):
    return RAGEvalCase(
        case_id="case-1",
        task="qa",
        query="Synthetic query",
        documents=(
            "one.txt",
        ),
        expected_documents=(
            "one.txt",
        ),
        required_facts=tuple(
            required_facts
        ),
        forbidden_facts=(),
        expected_abstention=(
            expected_abstention
        ),
    )


def test_resolve_case_document_ids():
    result = (
        FinalRAGRunner
        ._resolve_case_document_ids(
            case=_case(),
            document_id_map={
                "one.txt": "doc-1",
            },
        )
    )

    assert result == [
        "doc-1"
    ]


def test_resolve_case_document_ids_missing():
    try:
        (
            FinalRAGRunner
            ._resolve_case_document_ids(
                case=_case(),
                document_id_map={},
            )
        )
    except RuntimeError as exc:
        assert "one.txt" in str(
            exc
        )
    else:
        raise AssertionError(
            "Expected RuntimeError."
        )


def test_normalize_sources_adds_source_number():
    sources = (
        FinalRAGRunner
        ._normalize_sources(
            [
                {
                    "source": (
                        "one.txt"
                    ),
                    "text": "value",
                }
            ]
        )
    )

    assert (
        sources[0][
            "source_number"
        ]
        == 1
    )


def test_no_information_documented_is_abstention():
    result = (
        GenerationEvaluator
        .evaluate(
            case=_case(
                expected_abstention=True
            ),
            answer=(
                "There is no information "
                "documented about medication "
                "allergy in the provided "
                "context."
            ),
            grounded_is_valid=True,
        )
    )

    assert (
        result.abstention_correct
        is True
    )


def test_narrow_no_break_space_normalizes():
    result = (
        GenerationEvaluator
        .evaluate(
            case=_case(
                required_facts=(
                    "108 mg/dL",
                )
            ),
            answer=(
                "The value was "
                "108\u202fmg/dL."
            ),
            grounded_is_valid=True,
        )
    )

    assert (
        result.required_fact_recall
        == 1.0
    )

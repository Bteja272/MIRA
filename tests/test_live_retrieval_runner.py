from evaluation.live_retrieval_runner import (
    LiveRetrievalRunner,
)
from evaluation.models import (
    RAGEvalCase,
)


def _case(
    *,
    task: str = "qa",
) -> RAGEvalCase:
    return RAGEvalCase(
        case_id="case-1",
        task=task,
        query="Synthetic query",
        documents=(
            "one.txt",
            "two.txt",
        ),
        expected_documents=(
            "one.txt",
        ),
        required_facts=(),
        forbidden_facts=(),
        expected_abstention=False,
    )


def test_resolve_case_document_ids():
    case = _case()

    result = (
        LiveRetrievalRunner
        ._resolve_case_document_ids(
            case=case,
            document_id_map={
                "one.txt": "doc-1",
                "two.txt": "doc-2",
            },
        )
    )

    assert result == [
        "doc-1",
        "doc-2",
    ]


def test_resolve_case_document_ids_missing():
    case = _case()

    try:
        (
            LiveRetrievalRunner
            ._resolve_case_document_ids(
                case=case,
                document_id_map={
                    "one.txt": "doc-1",
                },
            )
        )
    except RuntimeError as exc:
        assert "two.txt" in str(exc)
    else:
        raise AssertionError(
            "Expected RuntimeError."
        )


def test_runner_rejects_invalid_top_k():
    try:
        LiveRetrievalRunner(
            user_id=None,
            top_k=0,
            context_token_budget=1000,
        )
    except ValueError as exc:
        assert "top_k" in str(exc)
    else:
        raise AssertionError(
            "Expected ValueError."
        )


def test_runner_rejects_invalid_context_budget():
    try:
        LiveRetrievalRunner(
            user_id=None,
            top_k=3,
            context_token_budget=0,
        )
    except ValueError as exc:
        assert (
            "context_token_budget"
            in str(exc)
        )
    else:
        raise AssertionError(
            "Expected ValueError."
        )

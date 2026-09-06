from pathlib import Path

import pytest
from langchain_core.documents import Document as LangChainDocument

from evaluation.dataset_loader import load_rag_eval_dataset
from evaluation.metrics import aggregate_retrieval_results
from evaluation.models import RAGEvalCase
from evaluation.retrieval_evaluator import RetrievalEvaluator


DATASET_PATH = (
    Path(__file__).resolve().parents[1]
    / "evaluation"
    / "datasets"
    / "rag_eval_cases.json"
)


def _document(*, source: str, text: str, chunk_index: int = 0):
    return LangChainDocument(
        page_content=text,
        metadata={
            "source": source,
            "document_id": f"id-{source}",
            "chunk_id": f"chunk-{source}-{chunk_index}",
            "chunk_index": chunk_index,
        },
    )


def _case(
    *,
    case_id: str = "case-1",
    expected_documents=("expected.txt",),
    required_facts=("11.2 g/dL",),
):
    return RAGEvalCase(
        case_id=case_id,
        task="qa",
        query="Synthetic query",
        documents=("expected.txt", "distractor.txt"),
        expected_documents=tuple(expected_documents),
        required_facts=tuple(required_facts),
        forbidden_facts=(),
        expected_abstention=False,
    )


def test_dataset_loads():
    dataset = load_rag_eval_dataset(DATASET_PATH)
    assert dataset.dataset_name == "mira_rag_eval_v1"
    assert len(dataset.cases) == 12
    assert len({case.case_id for case in dataset.cases}) == 12


def test_ranked_retrieval_perfect_hit():
    case = _case()
    result = RetrievalEvaluator.evaluate_ranked_retrieval(
        case=case,
        documents=[
            _document(source="expected.txt", text="Hemoglobin 11.2 g/dL"),
            _document(source="distractor.txt", text="Unrelated text"),
        ],
        k=2,
    )
    assert result.hit_at_k is True
    assert result.recall_at_k == 1.0
    assert result.reciprocal_rank == 1.0
    assert result.wrong_document_rate == 0.5


def test_ranked_retrieval_mrr_uses_first_expected_rank():
    case = _case()
    result = RetrievalEvaluator.evaluate_ranked_retrieval(
        case=case,
        documents=[
            _document(source="distractor.txt", text="Distractor"),
            _document(source="expected.txt", text="Hemoglobin 11.2 g/dL"),
        ],
        k=2,
    )
    assert result.hit_at_k is True
    assert result.reciprocal_rank == 0.5


def test_ranked_retrieval_miss():
    case = _case()
    result = RetrievalEvaluator.evaluate_ranked_retrieval(
        case=case,
        documents=[_document(source="distractor.txt", text="Distractor")],
        k=1,
    )
    assert result.hit_at_k is False
    assert result.recall_at_k == 0.0
    assert result.reciprocal_rank == 0.0
    assert result.wrong_document_rate == 1.0


def test_context_retains_required_evidence():
    case = _case()
    result = RetrievalEvaluator.evaluate_context(
        case=case,
        documents=[
            _document(
                source="expected.txt",
                text="Hemoglobin result: 11.2 g/dL.",
            )
        ],
    )
    assert result.document_recall == 1.0
    assert result.required_fact_survival_rate == 1.0
    assert result.expected_evidence_retained is True


def test_context_detects_lost_required_fact():
    case = _case()
    result = RetrievalEvaluator.evaluate_context(
        case=case,
        documents=[
            _document(
                source="expected.txt",
                text="Hemoglobin result was recorded.",
            )
        ],
    )
    assert result.document_recall == 1.0
    assert result.required_fact_survival_rate == 0.0
    assert result.expected_evidence_retained is False


def test_aggregate_retrieval_metrics():
    perfect = RetrievalEvaluator.evaluate_ranked_retrieval(
        case=_case(case_id="case-1"),
        documents=[_document(source="expected.txt", text="Expected")],
        k=1,
    )
    miss = RetrievalEvaluator.evaluate_ranked_retrieval(
        case=_case(case_id="case-2"),
        documents=[_document(source="distractor.txt", text="Wrong")],
        k=1,
    )

    summary = aggregate_retrieval_results([perfect, miss])

    assert summary["case_count"] == 2
    assert summary["hit_rate_at_k"] == 0.5
    assert summary["recall_at_k"] == 0.5
    assert summary["mrr"] == 0.5
    assert summary["wrong_document_rate"] == 0.5


def test_invalid_k_is_rejected():
    with pytest.raises(ValueError):
        RetrievalEvaluator.evaluate_ranked_retrieval(
            case=_case(),
            documents=[],
            k=0,
        )

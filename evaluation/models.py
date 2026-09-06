from __future__ import annotations

from dataclasses import dataclass
from typing import Any


SUPPORTED_TASKS = {"qa", "summarization", "comparison"}


def _clean_string_list(value: Any, *, field_name: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a list.")
    return tuple(str(item).strip() for item in value if str(item).strip())


@dataclass(frozen=True)
class RAGEvalCase:
    case_id: str
    task: str
    query: str
    documents: tuple[str, ...]
    expected_documents: tuple[str, ...]
    required_facts: tuple[str, ...]
    forbidden_facts: tuple[str, ...]
    expected_abstention: bool

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "RAGEvalCase":
        case_id = str(value.get("case_id", "")).strip()
        task = str(value.get("task", "")).strip()
        query = str(value.get("query", "")).strip()

        if not case_id:
            raise ValueError("case_id is required.")
        if task not in SUPPORTED_TASKS:
            raise ValueError(f"Unsupported task: {task}")
        if not query:
            raise ValueError(f"{case_id}: query is required.")

        documents = _clean_string_list(value.get("documents"), field_name="documents")
        expected_documents = _clean_string_list(
            value.get("expected_documents"),
            field_name="expected_documents",
        )

        if not documents:
            raise ValueError(f"{case_id}: documents cannot be empty.")
        if not expected_documents:
            raise ValueError(f"{case_id}: expected_documents cannot be empty.")

        if set(expected_documents) - set(documents):
            raise ValueError(
                f"{case_id}: expected_documents must also appear in documents."
            )

        expected_abstention = value.get("expected_abstention", False)
        if not isinstance(expected_abstention, bool):
            raise ValueError(
                f"{case_id}: expected_abstention must be boolean."
            )

        return cls(
            case_id=case_id,
            task=task,
            query=query,
            documents=documents,
            expected_documents=expected_documents,
            required_facts=_clean_string_list(
                value.get("required_facts"),
                field_name="required_facts",
            ),
            forbidden_facts=_clean_string_list(
                value.get("forbidden_facts"),
                field_name="forbidden_facts",
            ),
            expected_abstention=expected_abstention,
        )


@dataclass(frozen=True)
class RAGEvalDataset:
    dataset_name: str
    dataset_version: str
    description: str
    cases: tuple[RAGEvalCase, ...]

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "RAGEvalDataset":
        dataset_name = str(value.get("dataset_name", "")).strip()
        dataset_version = str(value.get("dataset_version", "")).strip()
        description = str(value.get("description", "")).strip()
        raw_cases = value.get("cases")

        if not dataset_name:
            raise ValueError("dataset_name is required.")
        if not dataset_version:
            raise ValueError("dataset_version is required.")
        if not isinstance(raw_cases, list):
            raise ValueError("cases must be a list.")

        cases = tuple(RAGEvalCase.from_dict(case) for case in raw_cases)
        if not cases:
            raise ValueError("At least one evaluation case is required.")

        case_ids = [case.case_id for case in cases]
        if len(case_ids) != len(set(case_ids)):
            raise ValueError("case_id values must be unique.")

        return cls(
            dataset_name=dataset_name,
            dataset_version=dataset_version,
            description=description,
            cases=cases,
        )


@dataclass(frozen=True)
class RetrievalCaseResult:
    case_id: str
    task: str
    k: int
    retrieved_sources: tuple[str, ...]
    expected_sources: tuple[str, ...]
    hit_at_k: bool
    recall_at_k: float
    reciprocal_rank: float
    wrong_document_rate: float


@dataclass(frozen=True)
class ContextCaseResult:
    case_id: str
    context_sources: tuple[str, ...]
    expected_sources: tuple[str, ...]
    document_recall: float
    required_fact_survival_rate: float
    expected_evidence_retained: bool

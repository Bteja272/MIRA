from __future__ import annotations

import re

from langchain_core.documents import Document as LangChainDocument

from evaluation.models import (
    ContextCaseResult,
    RAGEvalCase,
    RetrievalCaseResult,
)


class RetrievalEvaluator:
    @staticmethod
    def _normalize_text(value: str) -> str:
        return re.sub(
            r"\\s+",
            " ",
            (value or "").strip().casefold(),
        )

    @staticmethod
    def _source_name(document: LangChainDocument) -> str:
        metadata = document.metadata or {}
        source = metadata.get("source")
        return "" if source is None else str(source).strip()

    @classmethod
    def evaluate_ranked_retrieval(
        cls,
        *,
        case: RAGEvalCase,
        documents: list[LangChainDocument],
        k: int,
    ) -> RetrievalCaseResult:
        if k <= 0:
            raise ValueError("k must be greater than zero.")

        ranked_documents = documents[:k]
        retrieved_sources = tuple(
            source
            for source in (
                cls._source_name(document)
                for document in ranked_documents
            )
            if source
        )

        expected_sources = tuple(case.expected_documents)
        expected_set = set(expected_sources)

        retrieved_expected = {
            source
            for source in retrieved_sources
            if source in expected_set
        }

        recall_at_k = (
            len(retrieved_expected) / len(expected_set)
            if expected_set
            else 0.0
        )

        reciprocal_rank = 0.0
        for rank, source in enumerate(retrieved_sources, start=1):
            if source in expected_set:
                reciprocal_rank = 1.0 / rank
                break

        wrong_document_count = sum(
            1 for source in retrieved_sources if source not in expected_set
        )
        wrong_document_rate = (
            wrong_document_count / len(retrieved_sources)
            if retrieved_sources
            else 0.0
        )

        return RetrievalCaseResult(
            case_id=case.case_id,
            task=case.task,
            k=k,
            retrieved_sources=retrieved_sources,
            expected_sources=expected_sources,
            hit_at_k=bool(retrieved_expected),
            recall_at_k=recall_at_k,
            reciprocal_rank=reciprocal_rank,
            wrong_document_rate=wrong_document_rate,
        )

    @classmethod
    def evaluate_context(
        cls,
        *,
        case: RAGEvalCase,
        documents: list[LangChainDocument],
    ) -> ContextCaseResult:
        context_sources = tuple(
            dict.fromkeys(
                source
                for source in (
                    cls._source_name(document)
                    for document in documents
                )
                if source
            )
        )

        expected_sources = tuple(case.expected_documents)
        expected_set = set(expected_sources)
        context_expected = set(context_sources) & expected_set

        document_recall = (
            len(context_expected) / len(expected_set)
            if expected_set
            else 0.0
        )

        combined_context = cls._normalize_text(
            "\n".join(document.page_content for document in documents)
        )

        retained_facts = sum(
            1
            for fact in case.required_facts
            if cls._normalize_text(fact)
            and cls._normalize_text(fact) in combined_context
        )

        required_fact_survival_rate = (
            retained_facts / len(case.required_facts)
            if case.required_facts
            else 1.0
        )

        return ContextCaseResult(
            case_id=case.case_id,
            context_sources=context_sources,
            expected_sources=expected_sources,
            document_recall=document_recall,
            required_fact_survival_rate=required_fact_survival_rate,
            expected_evidence_retained=(
                document_recall == 1.0
                and required_fact_survival_rate == 1.0
            ),
        )

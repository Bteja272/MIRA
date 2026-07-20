import time

from app.core.config import settings
from app.services.langchain_retriever_service import (
    LangChainRetrieverService,
)
from app.services.llm_service import (
    LLMService,
)
from app.services.medical_prompt_service import (
    MedicalPromptService,
)
from app.services.prompt_service import (
    PromptService,
)


class RAGService:
    SUMMARY_KEYWORDS = (
        "summarize",
        "summarise",
        "summary",
        "overview",
        "give me an overview",
        "provide an overview",
        "what does this document say",
        "what is in this document",
    )

    COMPARISON_KEYWORDS = (
        "compare",
        "comparison",
        "difference",
        "differences",
        "changed",
        "changes",
        "trend",
        "trends",
        "over time",
        "between these",
        "across these",
        "earlier",
        "later",
    )

    @staticmethod
    def _normalize_document_ids(
        document_id: str | None = None,
        document_ids: list[str] | None = None,
    ) -> list[str]:
        selected: list[str] = []
        candidates: list[str] = []

        if document_id:
            candidates.append(
                document_id
            )

        if document_ids:
            candidates.extend(
                document_ids
            )

        for candidate in candidates:
            cleaned = candidate.strip()

            if (
                cleaned
                and cleaned not in selected
            ):
                selected.append(
                    cleaned
                )

        return selected

    @classmethod
    def _is_summary_query(
        cls,
        query: str,
    ) -> bool:
        normalized_query = (
            query.lower().strip()
        )

        return any(
            keyword in normalized_query
            for keyword
            in cls.SUMMARY_KEYWORDS
        )

    @classmethod
    def _is_comparison_query(
        cls,
        query: str,
    ) -> bool:
        normalized_query = (
            query.lower().strip()
        )

        return any(
            keyword in normalized_query
            for keyword
            in cls.COMPARISON_KEYWORDS
        )

    @classmethod
    def query(
        cls,
        query: str,
        document_id: str | None = None,
        document_ids: list[str] | None = None,
    ) -> dict:
        started_at = (
            time.perf_counter()
        )

        selected_ids = (
            cls._normalize_document_ids(
                document_id=document_id,
                document_ids=document_ids,
            )
        )

        is_summary = (
            cls._is_summary_query(
                query
            )
        )

        is_comparison = (
            cls._is_comparison_query(
                query
            )
        )

        if (
            not selected_ids
            and is_summary
        ):
            latest_document_id = (
                LangChainRetrieverService
                .get_latest_document_id(
                    user_id=None
                )
            )

            if latest_document_id:
                selected_ids = [
                    latest_document_id
                ]

        if len(selected_ids) > 1:
            documents = (
                LangChainRetrieverService
                .retrieve_documents(
                    document_ids=(
                        selected_ids
                    ),
                    user_id=None,
                )
            )

            task = (
                "comparison"
                if is_comparison
                else (
                    "multi_document_"
                    "overview"
                )
            )

        elif (
            len(selected_ids) == 1
            and is_summary
        ):
            documents = (
                LangChainRetrieverService
                .retrieve_document(
                    document_id=(
                        selected_ids[0]
                    ),
                    user_id=None,
                )
            )

            task = "summarization"

        else:
            documents = (
                LangChainRetrieverService
                .retrieve(
                    query=query,
                    top_k=(
                        settings
                        .retrieval_top_k
                    ),
                    document_ids=(
                        selected_ids or None
                    ),
                    user_id=None,
                )
            )

            task = "qa"

        selected_document_id = (
            selected_ids[0]
            if len(selected_ids) == 1
            else None
        )

        if not documents:
            answer = (
                "I could not find relevant "
                "information in the selected "
                "uploaded document or documents."
            )

            answer = (
                MedicalPromptService
                .ensure_disclaimer(
                    answer
                )
            )

            return {
                "query": query,
                "answer": answer,
                "document_id": (
                    selected_document_id
                ),
                "document_ids": (
                    selected_ids
                ),
                "selected_document_count": (
                    len(selected_ids)
                ),
                "sources": [],
                "latency_seconds": round(
                    time.perf_counter()
                    - started_at,
                    3,
                ),
            }

        prompt = (
            PromptService.build_prompt(
                query=query,
                documents=documents,
                task=task,
            )
        )

        answer = (
            LLMService.generate_response(
                prompt=prompt,
                system_prompt=(
                    MedicalPromptService
                    .document_system_prompt()
                ),
            )
        )

        answer = (
            MedicalPromptService
            .ensure_disclaimer(
                answer
            )
        )

        sources = (
            LangChainRetrieverService
            .to_source_dicts(
                documents
            )
        )

        return {
            "query": query,
            "answer": answer,
            "document_id": (
                selected_document_id
            ),
            "document_ids": selected_ids,
            "selected_document_count": (
                len(selected_ids)
            ),
            "sources": sources,
            "latency_seconds": round(
                time.perf_counter()
                - started_at,
                3,
            ),
        }
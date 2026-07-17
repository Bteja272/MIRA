import time

from app.core.config import settings
from app.services.langchain_retriever_service import (
    LangChainRetrieverService,
)
from app.services.llm_service import LLMService
from app.services.medical_prompt_service import (
    MedicalPromptService,
)
from app.services.prompt_service import PromptService


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

    @classmethod
    def _is_summary_query(
        cls,
        query: str,
    ) -> bool:
        normalized_query = query.lower().strip()

        return any(
            keyword in normalized_query
            for keyword in cls.SUMMARY_KEYWORDS
        )

    @classmethod
    def query(
        cls,
        query: str,
        document_id: str | None = None,
    ) -> dict:
        started_at = time.perf_counter()

        is_summary = cls._is_summary_query(query)
        selected_document_id = document_id

        # Summaries should operate on one complete document.
        if is_summary and not selected_document_id:
            selected_document_id = (
                LangChainRetrieverService
                .get_latest_document_id()
            )

        if is_summary and selected_document_id:
            documents = (
                LangChainRetrieverService
                .retrieve_document(
                    document_id=selected_document_id,
                )
            )
            task = "summarization"
        else:
            documents = (
                LangChainRetrieverService.retrieve(
                    query=query,
                    top_k=settings.retrieval_top_k,
                    document_id=selected_document_id,
                )
            )
            task = "qa"

        if not documents:
            answer = (
                "I could not find relevant information in the "
                "selected uploaded document."
            )

            answer = (
                MedicalPromptService
                .ensure_disclaimer(answer)
            )

            return {
                "query": query,
                "answer": answer,
                "document_id": selected_document_id,
                "sources": [],
                "latency_seconds": round(
                    time.perf_counter() - started_at,
                    3,
                ),
            }

        prompt = PromptService.build_prompt(
            query=query,
            documents=documents,
            task=task,
        )

        answer = LLMService.generate_response(
            prompt=prompt,
            system_prompt=(
                MedicalPromptService
                .document_system_prompt()
            ),
        )

        answer = (
            MedicalPromptService
            .ensure_disclaimer(answer)
        )

        sources = (
            LangChainRetrieverService
            .to_source_dicts(documents)
        )

        return {
            "query": query,
            "answer": answer,
            "document_id": selected_document_id,
            "sources": sources,
            "latency_seconds": round(
                time.perf_counter() - started_at,
                3,
            ),
        }
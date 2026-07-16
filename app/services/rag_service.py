import time

from app.core.config import settings
from app.core.logger import logger
from app.services.langchain_retriever_service import (
    LangChainRetrieverService,
)
from app.services.llm_service import LLMService
from app.services.prompt_service import PromptService


class RAGService:
    SUMMARY_KEYWORDS = (
        "summarize",
        "summary",
        "overview",
        "give me a summary",
        "summarise",
    )

    @classmethod
    def _is_summary_request(cls, query: str) -> bool:
        query_lower = query.lower()

        return any(
            keyword in query_lower
            for keyword in cls.SUMMARY_KEYWORDS
        )

    @staticmethod
    def _empty_result(
        query: str,
        message: str,
        latency: float,
        document_id: str | None,
    ) -> dict:
        return {
            "query": query,
            "answer": message,
            "document_id": document_id,
            "sources": [],
            "latency_seconds": latency,
        }

    @classmethod
    def query(
        cls,
        query: str,
        document_id: str | None = None,
    ) -> dict:
        start_time = time.time()
        selected_document_id = document_id
        is_summary = cls._is_summary_request(query)

        if is_summary:
            if selected_document_id is None:
                selected_document_id = (
                    LangChainRetrieverService
                    .get_latest_document_id()
                )

            if selected_document_id is None:
                latency = round(time.time() - start_time, 3)

                return cls._empty_result(
                    query=query,
                    message=(
                        "No indexed document was found to summarize."
                    ),
                    latency=latency,
                    document_id=None,
                )

            documents = (
                LangChainRetrieverService.retrieve_document(
                    selected_document_id
                )
            )
            task = "summarization"

        else:
            documents = LangChainRetrieverService.retrieve(
                query=query,
                top_k=settings.retrieval_top_k,
                document_id=selected_document_id,
            )
            task = "question_answering"

        chunks = LangChainRetrieverService.to_source_dicts(
            documents
        )

        if not chunks:
            latency = round(time.time() - start_time, 3)

            return cls._empty_result(
                query=query,
                message=(
                    "No relevant indexed document content was found."
                ),
                latency=latency,
                document_id=selected_document_id,
            )

        prompt = PromptService.build_prompt(
            query=query,
            context_chunks=chunks,
            task=task,
        )

        answer = LLMService.generate_response(prompt)
        latency = round(time.time() - start_time, 3)

        logger.info("Query processed")
        logger.info(f"Query: {query}")
        logger.info(
            f"Document ID: {selected_document_id}"
        )
        logger.info(f"Retrieved chunks: {len(chunks)}")
        logger.info(f"Latency: {latency}s")

        return {
            "query": query,
            "answer": answer,
            "document_id": selected_document_id,
            "sources": chunks,
            "latency_seconds": latency,
        }
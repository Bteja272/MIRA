import time

from app.core.config import settings
from app.core.logger import logger
from app.services.llm_service import LLMService
from app.services.prompt_service import PromptService
from app.services.langchain_retriever_service import LangChainRetrieverService


class RAGService:
    @staticmethod
    def query(query: str) -> dict:
        start_time = time.time()

        documents = LangChainRetrieverService.retrieve(
            query=query,
            top_k=settings.retrieval_top_k,
        )

        chunks = LangChainRetrieverService.to_source_dicts(documents)

        prompt = PromptService.build_prompt(query=query, context_chunks=chunks)
        answer = LLMService.generate_response(prompt)

        latency = round(time.time() - start_time, 3)

        logger.info("Query processed")
        logger.info(f"Query: {query}")
        logger.info(f"Retrieved chunks: {len(chunks)}")
        logger.info(f"Latency: {latency}s")

        return {
            "query": query,
            "answer": answer,
            "sources": chunks,
            "latency_seconds": latency,
        }
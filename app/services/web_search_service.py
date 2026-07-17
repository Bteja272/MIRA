import time

from tavily import TavilyClient

from app.core.config import settings
from app.core.logger import logger
from app.services.llm_service import LLMService
from app.services.medical_prompt_service import (
    MedicalPromptService,
)


class WebSearchService:
    MAX_RESULTS = 3
    MAX_CONTENT_CHARACTERS = 1500

    @classmethod
    def query(
        cls,
        query: str,
    ) -> dict:
        started_at = time.perf_counter()

        if not settings.tavily_api_key:
            raise RuntimeError(
                "TAVILY_API_KEY is not configured."
            )

        client = TavilyClient(
            api_key=settings.tavily_api_key
        )

        search_response = client.search(
            query=query,
            search_depth="advanced",
            max_results=cls.MAX_RESULTS,
        )

        results = search_response.get(
            "results",
            [],
        )

        if not results:
            answer = (
                "No relevant current web sources were found "
                "for this question."
            )

            answer = (
                MedicalPromptService
                .ensure_disclaimer(answer)
            )

            return {
                "query": query,
                "answer": answer,
                "sources": [],
                "latency_seconds": round(
                    time.perf_counter() - started_at,
                    3,
                ),
            }

        context_parts: list[str] = []
        source_records: list[dict] = []

        for index, result in enumerate(
            results,
            start=1,
        ):
            title = (
                result.get("title")
                or "Untitled source"
            )
            url = (
                result.get("url")
                or "Unavailable"
            )
            raw_content = (
                result.get("content")
                or ""
            )

            trimmed_content = raw_content[
                :cls.MAX_CONTENT_CHARACTERS
            ]

            context_parts.append(
                (
                    f"[Web Source {index}]\n"
                    f"Title: {title}\n"
                    f"URL: {url}\n"
                    f"Content:\n{trimmed_content}"
                )
            )

            source_records.append(
                {
                    "source_number": index,
                    "title": title,
                    "url": url,
                    "content": trimmed_content,
                }
            )

        context = "\n\n".join(context_parts)

        prompt = f"""
Use only the following current web-search context to answer the user's
question.

Cite supporting information using labels such as [Web Source 1].

Do not invent information that is not present in the sources.

WEB CONTEXT
{context}

USER QUESTION
{query}

ANSWER
""".strip()

        logger.info(
            "Web synthesis prompt contains %s characters "
            "across %s sources",
            len(prompt),
            len(results),
        )

        answer = LLMService.generate_response(
            prompt=prompt,
            system_prompt=(
                MedicalPromptService
                .web_system_prompt()
            ),
        )

        answer = (
            MedicalPromptService
            .ensure_disclaimer(answer)
        )

        return {
            "query": query,
            "answer": answer,
            "sources": source_records,
            "latency_seconds": round(
                time.perf_counter() - started_at,
                3,
            ),
        }
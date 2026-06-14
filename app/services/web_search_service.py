from tavily import TavilyClient

from app.core.config import settings
from app.services.llm_service import LLMService


class WebSearchService:
    @staticmethod
    def query(query: str):
        client = TavilyClient(
            api_key=settings.tavily_api_key
        )

        search_results = client.search(
            query=query,
            search_depth="advanced",
            max_results=5,
        )

        results = search_results.get("results", [])

        context = "\n\n".join(
            [
                f"Title: {result.get('title')}\n"
                f"Content: {result.get('content')}"
                for result in results
            ]
        )

        prompt = f"""
Answer the user's question using the search results below.

Question:
{query}

Search Results:
{context}

Provide a concise and accurate answer.
""".strip()

        answer = LLMService.generate_response(prompt)

        return {
            "route": "web_search",
            "query": query,
            "answer": answer,
            "sources": [
                {
                    "title": result.get("title"),
                    "url": result.get("url"),
                }
                for result in results
            ],
        }
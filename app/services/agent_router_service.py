from app.services.direct_llm_service import DirectLLMService
from app.services.rag_service import RAGService
from app.services.web_search_service import WebSearchService


class AgentRouterService:

    @staticmethod
    def classify(query: str) -> str:
        query_lower = query.lower()

        rag_keywords = [
            "document",
            "pdf",
            "uploaded",
            "file",
            "according to",
            "source",
        ]

        web_keywords = [
            "latest",
            "today",
            "current",
            "news",
            "recent",
        ]

        if any(
            keyword in query_lower
            for keyword in rag_keywords
        ):
            return "rag"

        if any(
            keyword in query_lower
            for keyword in web_keywords
        ):
            return "web"

        return "direct"

    @classmethod
    def query(cls, query: str):
        route = cls.classify(query)

        if route == "rag":
            result = RAGService.query(query)
            result["route"] = "rag"
            return result

        if route == "web":
            return WebSearchService.query(query)

        return DirectLLMService.query(query)
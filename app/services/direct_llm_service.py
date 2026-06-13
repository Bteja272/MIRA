from app.services.llm_service import LLMService


class DirectLLMService:
    @staticmethod
    def query(query: str):
        answer = LLMService.generate_response(query)

        return {
            "route": "direct_llm",
            "query": query,
            "answer": answer,
            "sources": [],
        }
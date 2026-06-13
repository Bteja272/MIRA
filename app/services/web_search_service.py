class WebSearchService:
    @staticmethod
    def query(query: str):
        return {
            "route": "web_search",
            "query": query,
            "answer": (
                "Web search tool not configured yet."
            ),
            "sources": [],
        }
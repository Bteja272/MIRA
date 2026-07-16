from typing import TypedDict

from langgraph.graph import StateGraph, END

from app.services.direct_llm_service import DirectLLMService
from app.services.llm_service import LLMService
from app.services.rag_service import RAGService
from app.services.web_search_service import WebSearchService


class AgentState(TypedDict):
    query: str
    document_id: str | None
    route: str
    result: dict


def classify_node(state: AgentState):
    query = state["query"]

    classifier_prompt = f"""
You are a query-routing classifier for an agentic RAG system.

Choose exactly one route:

rag:
Use this when the user asks about uploaded documents, PDFs, files, sources,
or asks "according to the document".

direct:
Use this when the user asks a general explanation, coding concept,
definition, or reasoning question that does not require uploaded documents
or current external information.

web:
Use this when the user asks for latest, current, recent, today, news,
live, updated, or real-world information that may have changed recently.

Return only one word:
rag
direct
web

User query:
{query}
""".strip()

    try:
        route = LLMService.generate_response(classifier_prompt)
        route = route.strip().lower()

        if route not in {"rag", "direct", "web"}:
            route = fallback_classify(query)

    except Exception:
        route = fallback_classify(query)

    return {
        **state,
        "route": route,
    }


def fallback_classify(query: str) -> str:
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
        "live",
        "updated",
    ]

    if any(keyword in query_lower for keyword in rag_keywords):
        return "rag"

    if any(keyword in query_lower for keyword in web_keywords):
        return "web"

    return "direct"


def rag_node(state: AgentState):
    result = RAGService.query(
        query=state["query"],
        document_id=state.get("document_id"),
    )
    result["route"] = "rag"

    return {
        **state,
        "result": result,
    }


def direct_node(state: AgentState):
    result = DirectLLMService.query(state["query"])

    return {
        **state,
        "result": result,
    }


def web_node(state: AgentState):
    result = WebSearchService.query(state["query"])

    return {
        **state,
        "result": result,
    }


def router(state: AgentState):
    return state["route"]


graph = StateGraph(AgentState)

graph.add_node("classifier", classify_node)
graph.add_node("rag", rag_node)
graph.add_node("direct", direct_node)
graph.add_node("web", web_node)

graph.set_entry_point("classifier")

graph.add_conditional_edges(
    "classifier",
    router,
    {
        "rag": "rag",
        "direct": "direct",
        "web": "web",
    },
)

graph.add_edge("rag", END)
graph.add_edge("direct", END)
graph.add_edge("web", END)

agent_graph = graph.compile()


class LangGraphAgentService:
    @staticmethod
    def query(
        query: str,
        document_id: str | None = None,
    ):
        result = agent_graph.invoke(
            {
                "query": query,
                "document_id": document_id,
                "route": "",
                "result": {},
            }
        )

        return result["result"]
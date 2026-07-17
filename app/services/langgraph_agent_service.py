from typing import TypedDict

from langgraph.graph import END, StateGraph

from app.services.direct_llm_service import DirectLLMService
from app.services.llm_service import LLMService
from app.services.rag_service import RAGService
from app.services.safety_guard import SafetyGuard
from app.services.web_search_service import WebSearchService


class AgentState(TypedDict, total=False):
    query: str
    document_id: str | None
    route: str
    result: dict
    safety_status: str
    safety_category: str
    safety_response: str | None


def safety_node(state: AgentState):
    decision = SafetyGuard.evaluate(state["query"])

    return {
        **state,
        "safety_status": (
            "allowed" if decision.allowed else "blocked"
        ),
        "safety_category": decision.category,
        "safety_response": decision.response,
    }


def safety_router(state: AgentState):
    return state["safety_status"]


def safety_response_node(state: AgentState):
    return {
        **state,
        "result": {
            "route": "safety_guard",
            "query": state["query"],
            "answer": state.get("safety_response"),
            "sources": [],
            "safety_category": state.get("safety_category"),
        },
    }


def classify_node(state: AgentState):
    query = state["query"]

    classifier_prompt = f"""
You are a query-routing classifier for an agentic RAG system.

Choose exactly one route:

rag:
Use this when the user asks about uploaded documents, PDFs, files,
sources, medical records, lab reports, prescriptions, discharge
summaries, or asks "according to the document".

direct:
Use this when the user asks a general explanation, coding concept,
definition, medical term, or reasoning question that does not require
uploaded documents or current external information.

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
        route = LLMService.generate_response(
            classifier_prompt
        ).strip().lower()

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
        "medical record",
        "lab report",
        "prescription",
        "discharge summary",
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

graph.add_node("safety", safety_node)
graph.add_node("safety_block", safety_response_node)
graph.add_node("classifier", classify_node)
graph.add_node("rag", rag_node)
graph.add_node("direct", direct_node)
graph.add_node("web", web_node)

graph.set_entry_point("safety")

graph.add_conditional_edges(
    "safety",
    safety_router,
    {
        "allowed": "classifier",
        "blocked": "safety_block",
    },
)

graph.add_conditional_edges(
    "classifier",
    router,
    {
        "rag": "rag",
        "direct": "direct",
        "web": "web",
    },
)

graph.add_edge("safety_block", END)
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
                "safety_status": "",
                "safety_category": "",
                "safety_block": None,
            }
        )

        return result["result"]
from typing import TypedDict

from langgraph.graph import StateGraph, END

from app.services.direct_llm_service import DirectLLMService
from app.services.rag_service import RAGService
from app.services.web_search_service import WebSearchService


class AgentState(TypedDict):
    query: str
    route: str
    result: dict


def classify_node(state: AgentState):
    query = state["query"].lower()

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

    if any(k in query for k in rag_keywords):
        route = "rag"
    elif any(k in query for k in web_keywords):
        route = "web"
    else:
        route = "direct"

    return {
        **state,
        "route": route,
    }


def rag_node(state: AgentState):
    result = RAGService.query(state["query"])
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
    def query(query: str):
        result = agent_graph.invoke(
            {
                "query": query,
                "route": "",
                "result": {},
            }
        )

        return result["result"]
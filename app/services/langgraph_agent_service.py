from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

from app.services.direct_llm_service import (
    DirectLLMService,
)
from app.services.llm_service import LLMService
from app.services.rag_service import RAGService
from app.services.safety_guard import SafetyGuard
from app.services.web_search_service import (
    WebSearchService,
)


class AgentState(TypedDict, total=False):
    """
    State shared across the LangGraph workflow.

    document_ids must be declared here. Otherwise, LangGraph may discard
    it when the graph processes the initial input.
    """

    query: str
    document_ids: list[str]

    route: str
    result: dict

    safety_status: str
    safety_category: str
    safety_response: str


def _decision_value(
    decision: Any,
    names: tuple[str, ...],
    default: Any = None,
) -> Any:
    """
    Read a value from either a dictionary or dataclass-like object.
    """
    for name in names:
        if isinstance(decision, dict):
            if name in decision:
                return decision[name]

        elif hasattr(decision, name):
            return getattr(
                decision,
                name,
            )

    return default


def _run_safety_guard(
    query: str,
):
    """
    Support the current SafetyGuard without depending on one specific
    public method name.
    """
    for method_name in (
        "evaluate",
        "assess",
        "check",
    ):
        method = getattr(
            SafetyGuard,
            method_name,
            None,
        )

        if callable(method):
            return method(query)

    raise RuntimeError(
        "SafetyGuard must expose evaluate(), assess(), or check()."
    )


def safety_node(
    state: AgentState,
) -> dict:
    decision = _run_safety_guard(
        state["query"]
    )

    allowed = _decision_value(
        decision,
        (
            "allowed",
            "is_allowed",
            "safe",
            "is_safe",
        ),
        True,
    )

    category = _decision_value(
        decision,
        (
            "category",
            "safety_category",
        ),
        "allowed",
    )

    response = _decision_value(
        decision,
        (
            "response",
            "message",
            "user_message",
        ),
        "",
    )

    # Return only updated fields. LangGraph retains query and
    # document_ids because both are declared in AgentState.
    return {
        "safety_status": (
            "allowed"
            if bool(allowed)
            else "blocked"
        ),
        "safety_category": str(category),
        "safety_response": str(
            response or ""
        ),
    }


def safety_route(
    state: AgentState,
) -> str:
    if (
        state.get("safety_status")
        == "blocked"
    ):
        return "blocked"

    return "allowed"


def safety_block_node(
    state: AgentState,
) -> dict:
    selected_ids = (
        state.get("document_ids")
        or []
    )

    return {
        "route": "safety_guard",
        "result": {
            "query": state["query"],
            "answer": state.get(
                "safety_response",
                "",
            ),
            "document_id": (
                selected_ids[0]
                if len(selected_ids) == 1
                else None
            ),
            "document_ids": selected_ids,
            "selected_document_count": (
                len(selected_ids)
            ),
            "sources": [],
            "safety_category": state.get(
                "safety_category"
            ),
        },
    }


def fallback_classify(
    query: str,
) -> str:
    normalized_query = query.lower()

    document_keywords = (
        "document",
        "documents",
        "uploaded",
        "upload",
        "file",
        "files",
        "pdf",
        "report",
        "reports",
        "according to",
        "source",
        "summarize",
        "summarise",
        "summary",
        "overview",
        "compare",
        "comparison",
        "lab report",
        "discharge summary",
        "medical record",
        "prescription",
    )

    web_keywords = (
        "latest",
        "current",
        "recent",
        "today",
        "this week",
        "news",
        "updated",
        "live",
        "new study",
    )

    if any(
        keyword in normalized_query
        for keyword in document_keywords
    ):
        return "rag"

    if any(
        keyword in normalized_query
        for keyword in web_keywords
    ):
        return "web"

    return "direct"


def classify_node(
    state: AgentState,
) -> dict:
    query = state["query"]

    selected_ids = (
        state.get("document_ids")
        or []
    )

    # Explicit document selection always uses RAG.
    if selected_ids:
        return {
            "route": "rag",
        }

    deterministic_route = (
        fallback_classify(query)
    )

    if deterministic_route in {
        "rag",
        "web",
    }:
        return {
            "route": deterministic_route,
        }

    classifier_prompt = f"""
Classify the user query into exactly one route.

Routes:

rag
Use this for uploaded documents, medical records, files, and reports.

direct
Use this for general educational information that does not require
uploaded documents or current external information.

web
Use this for current, recent, live, or time-sensitive information.

Return only one word:

rag
direct
web

User query:
{query}
""".strip()

    try:
        route = (
            LLMService.generate_response(
                prompt=classifier_prompt,
                system_prompt=(
                    "You are a strict query-routing classifier. "
                    "Return only rag, direct, or web."
                ),
            )
            .strip()
            .lower()
        )

        if route not in {
            "rag",
            "direct",
            "web",
        }:
            route = deterministic_route

    except Exception:
        route = deterministic_route

    return {
        "route": route,
    }


def classifier_route(
    state: AgentState,
) -> str:
    return state.get(
        "route",
        "direct",
    )


def rag_node(
    state: AgentState,
) -> dict:
    selected_ids = (
        state.get("document_ids")
        or []
    )

    result = RAGService.query(
        query=state["query"],
        document_ids=selected_ids,
    )

    return {
        "result": result,
    }


def direct_node(
    state: AgentState,
) -> dict:
    result = DirectLLMService.query(
        state["query"]
    )

    return {
        "result": result,
    }


def web_node(
    state: AgentState,
) -> dict:
    result = WebSearchService.query(
        state["query"]
    )

    return {
        "result": result,
    }


graph_builder = StateGraph(
    AgentState
)

graph_builder.add_node(
    "safety",
    safety_node,
)

graph_builder.add_node(
    "safety_block",
    safety_block_node,
)

graph_builder.add_node(
    "classifier",
    classify_node,
)

graph_builder.add_node(
    "rag",
    rag_node,
)

graph_builder.add_node(
    "direct",
    direct_node,
)

graph_builder.add_node(
    "web",
    web_node,
)

graph_builder.set_entry_point(
    "safety"
)

graph_builder.add_conditional_edges(
    "safety",
    safety_route,
    {
        "allowed": "classifier",
        "blocked": "safety_block",
    },
)

graph_builder.add_conditional_edges(
    "classifier",
    classifier_route,
    {
        "rag": "rag",
        "direct": "direct",
        "web": "web",
    },
)

graph_builder.add_edge(
    "safety_block",
    END,
)

graph_builder.add_edge(
    "rag",
    END,
)

graph_builder.add_edge(
    "direct",
    END,
)

graph_builder.add_edge(
    "web",
    END,
)

agent_graph = graph_builder.compile()


class LangGraphAgentService:
    @staticmethod
    def _normalize_document_ids(
        document_id: str | None = None,
        document_ids: list[str] | None = None,
    ) -> list[str]:
        selected_ids: list[str] = []
        candidates: list[str] = []

        if document_id:
            candidates.append(
                document_id
            )

        if document_ids:
            candidates.extend(
                document_ids
            )

        for candidate in candidates:
            cleaned = candidate.strip()

            if (
                cleaned
                and cleaned not in selected_ids
            ):
                selected_ids.append(
                    cleaned
                )

        return selected_ids

    @classmethod
    def query(
        cls,
        query: str,
        document_id: str | None = None,
        document_ids: list[str] | None = None,
    ) -> dict:
        selected_ids = (
            cls._normalize_document_ids(
                document_id=document_id,
                document_ids=document_ids,
            )
        )

        final_state = agent_graph.invoke(
            {
                "query": query,
                "document_ids": selected_ids,
            }
        )

        result = final_state.get(
            "result",
            {},
        )

        if not isinstance(result, dict):
            result = {
                "answer": str(result),
            }

        # Use assignment rather than setdefault so stale or incorrect
        # values cannot override the actual request selection.
        result["query"] = query

        result["document_id"] = (
            selected_ids[0]
            if len(selected_ids) == 1
            else None
        )

        result["document_ids"] = (
            selected_ids
        )

        result[
            "selected_document_count"
        ] = len(selected_ids)

        result["route"] = (
            final_state.get(
                "route",
                "direct",
            )
        )

        if (
            final_state.get(
                "safety_status"
            )
            == "blocked"
        ):
            result["route"] = (
                "safety_guard"
            )

            result[
                "safety_category"
            ] = final_state.get(
                "safety_category"
            )

        return result
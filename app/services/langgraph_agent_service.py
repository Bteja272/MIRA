from typing import (
    Any,
    TypedDict,
)

from langgraph.graph import (
    END,
    StateGraph,
)

from app.services.direct_llm_service import (
    DirectLLMService,
)
from app.services.rag_service import (
    RAGService,
)
from app.services.safety_guard import (
    SafetyGuard,
)
from app.services.web_search_service import (
    WebSearchService,
)


class AgentState(
    TypedDict,
    total=False,
):
    query: str
    retrieval_query: str

    document_ids: list[str]
    user_id: str | None

    conversation_context: list[
        dict[str, str]
    ]

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
    for name in names:
        if isinstance(
            decision,
            dict,
        ):
            if name in decision:
                return decision[name]

        elif hasattr(
            decision,
            name,
        ):
            return getattr(
                decision,
                name,
            )

    return default


def _run_safety_guard(
    query: str,
):
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
        "SafetyGuard must expose "
        "evaluate(), assess(), or check()."
    )


def safety_node(
    state: AgentState,
) -> dict:
    # Deliberately evaluate only the current
    # user request. Conversation history is
    # not permitted to alter pre-routing
    # safety behavior.
    decision = (
        _run_safety_guard(
            state["query"]
        )
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

    return {
        "safety_status": (
            "allowed"
            if bool(allowed)
            else "blocked"
        ),
        "safety_category": str(
            category
        ),
        "safety_response": str(
            response or ""
        ),
    }


def safety_route(
    state: AgentState,
) -> str:
    if (
        state.get(
            "safety_status"
        )
        == "blocked"
    ):
        return "blocked"

    return "allowed"


def safety_block_node(
    state: AgentState,
) -> dict:
    selected_ids = (
        state.get(
            "document_ids"
        )
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
            "document_ids": (
                selected_ids
            ),
            "selected_document_count": (
                len(selected_ids)
            ),
            "sources": [],
            "safety_category": (
                state.get(
                    "safety_category"
                )
            ),
        },
    }


def _normalize_query(
    query: str,
) -> str:
    return " ".join(
        query.lower().split()
    )


def _contains_any(
    query: str,
    phrases: tuple[str, ...],
) -> bool:
    return any(
        phrase in query
        for phrase in phrases
    )


def _is_web_freshness_query(
    normalized_query: str,
) -> bool:
    web_keywords = (
        "latest",
        "current",
        "recent",
        "today",
        "this week",
        "this month",
        "this year",
        "news",
        "updated",
        "live",
        "new study",
        "new studies",
        "recent study",
        "recent studies",
        "current guideline",
        "current guidelines",
        "latest guideline",
        "latest guidelines",
    )

    return _contains_any(
        normalized_query,
        web_keywords,
    )


def _is_explicit_web_query(
    normalized_query: str,
) -> bool:
    explicit_web_phrases = (
        "search the web",
        "search online",
        "look this up online",
        "look it up online",
        "check the web",
        "check online",
        "find online",
        "from the web",
        "on the web",
    )

    return _contains_any(
        normalized_query,
        explicit_web_phrases,
    )


def _is_document_specific_query(
    normalized_query: str,
) -> bool:
    """
    Return True when the wording asks for facts,
    values, comparisons, or interpretation tied to
    the selected report/document.

    These requests should stay document-grounded
    because patient-specific facts must come from
    the owned source material, not the web.
    """

    document_phrases = (
        "this document",
        "the document",
        "this report",
        "the report",
        "my report",
        "my document",
        "selected document",
        "selected documents",
        "uploaded document",
        "uploaded documents",
        "according to",
        "from the document",
        "from the report",
        "in the document",
        "in the report",
        "summarize",
        "summarise",
        "summary",
        "what is my",
        "what are my",
        "what was my",
        "what were my",
        "my result",
        "my results",
        "my level",
        "my levels",
        "my value",
        "my values",
        "my medication",
        "my medications",
        "my diagnosis",
        "my diagnoses",
        "reference range",
        "normal range",
        "within range",
        "within the range",
        "outside the range",
        "above range",
        "below range",
        "high or low",
        "is it high",
        "is it low",
        "is this high",
        "is this low",
        "safe level",
        "safe levels",
        "is my",
        "compare my",
        "compare this",
        "compare these",
        "first result",
        "second result",
        "third result",
        "fourth result",
        "fifth result",
    )

    return _contains_any(
        normalized_query,
        document_phrases,
    )


def _is_educational_expansion_query(
    normalized_query: str,
) -> bool:
    """
    Detect general educational questions that should
    not be trapped inside RAG merely because the user
    currently has a document selected.

    Examples:
      - What is hemoglobin?
      - What does LDL mean?
      - Explain hemoglobin A1c.
      - What is A1c used for?

    Patient-specific wording is handled separately by
    _is_document_specific_query().
    """

    definition_prefixes = (
        "what is ",
        "what are ",
        "what does ",
        "what do ",
        "define ",
        "explain ",
        "explain what ",
        "tell me about ",
        "what is the meaning of ",
        "what does it mean",
        "what is it used for",
        "what is this used for",
        "why is ",
        "why are ",
        "how does ",
        "how do ",
    )

    return normalized_query.startswith(
        definition_prefixes
    )


def fallback_classify(
    query: str,
) -> str:
    normalized_query = (
        _normalize_query(
            query
        )
    )

    if (
        _is_web_freshness_query(
            normalized_query
        )
        or _is_explicit_web_query(
            normalized_query
        )
    ):
        return "web"

    return "direct"


def classify_node(
    state: AgentState,
) -> dict:
    selected_ids = (
        state.get(
            "document_ids"
        )
        or []
    )

    normalized_query = (
        _normalize_query(
            state["query"]
        )
    )

    # Explicit web/freshness intent always wins after
    # the deterministic SafetyGuard has allowed the
    # current request.
    if (
        _is_web_freshness_query(
            normalized_query
        )
        or _is_explicit_web_query(
            normalized_query
        )
    ):
        return {
            "route": "web",
        }

    if selected_ids:
        # Patient/report-specific values, ranges,
        # comparisons and summaries remain grounded
        # in the selected owned documents.
        if _is_document_specific_query(
            normalized_query
        ):
            return {
                "route": "rag",
            }

        # A selected document is context, not a hard
        # "RAG mode". General definitions and medical
        # concept explanations may use web-backed
        # educational information without requiring
        # the user to deselect their report.
        if _is_educational_expansion_query(
            normalized_query
        ):
            return {
                "route": "web",
            }

        # Unknown intent with selected documents stays
        # conservative and grounded.
        return {
            "route": "rag",
        }

    return {
        "route": fallback_classify(
            state["query"]
        ),
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
        state.get(
            "document_ids"
        )
        or []
    )

    result = RAGService.query(
        query=state["query"],
        retrieval_query=(
            state.get(
                "retrieval_query"
            )
        ),
        document_ids=selected_ids,
        user_id=state.get(
            "user_id"
        ),
        conversation_context=(
            state.get(
                "conversation_context"
            )
            or []
        ),
    )

    return {
        "result": result,
    }


def direct_node(
    state: AgentState,
) -> dict:
    result = (
        DirectLLMService.query(
            query=state["query"],
            conversation_context=(
                state.get(
                    "conversation_context"
                )
                or []
            ),
        )
    )

    return {
        "result": result,
    }


def web_node(
    state: AgentState,
) -> dict:
    result = (
        WebSearchService.query(
            state.get(
                "retrieval_query"
            )
            or state["query"]
        )
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

agent_graph = (
    graph_builder.compile()
)


class LangGraphAgentService:
    @staticmethod
    def _normalize_document_ids(
        document_id: str | None = None,
        document_ids: (
            list[str] | None
        ) = None,
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
            cleaned = (
                candidate.strip()
            )

            if (
                cleaned
                and cleaned
                not in selected_ids
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
        document_ids: (
            list[str] | None
        ) = None,
        user_id: str | None = None,
        conversation_context: (
            list[dict[str, str]]
            | None
        ) = None,
        retrieval_query: (
            str | None
        ) = None,
    ) -> dict:
        selected_ids = (
            cls
            ._normalize_document_ids(
                document_id=(
                    document_id
                ),
                document_ids=(
                    document_ids
                ),
            )
        )

        final_state = (
            agent_graph.invoke(
                {
                    "query": query,
                    "retrieval_query": (
                        retrieval_query
                        or query
                    ),
                    "document_ids": (
                        selected_ids
                    ),
                    "user_id": user_id,
                    "conversation_context": (
                        conversation_context
                        or []
                    ),
                }
            )
        )

        result = final_state.get(
            "result",
            {},
        )

        if not isinstance(
            result,
            dict,
        ):
            result = {
                "answer": str(result),
            }

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
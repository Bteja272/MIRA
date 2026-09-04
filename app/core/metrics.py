from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Histogram,
    generate_latest,
)


# ---------------------------------------------------------
# Bounded label values
# ---------------------------------------------------------

AGENT_ROUTES = frozenset(
    {
        "rag",
        "direct",
        "web",
        "safety_guard",
    }
)

AGENT_NODES = frozenset(
    {
        "safety",
        "rag",
        "direct",
        "web",
    }
)

QUERY_FAILURE_STAGES = frozenset(
    {
        "validation",
        "conversation_load",
        "agent",
        "persistence",
    }
)

SAFETY_OUTCOMES = frozenset(
    {
        "allowed",
        "blocked",
    }
)

SAFETY_CATEGORIES = frozenset(
    {
        "allowed",
        "invalid_query",
        "self_harm",
        "emergency",
        "medication_request",
        "prognosis_request",
        "third_party_request",
        "diagnosis_request",
    }
)


# ---------------------------------------------------------
# Label normalization
# ---------------------------------------------------------

def normalize_agent_route(
    route: str | None,
) -> str:
    normalized = (
        str(route or "")
        .strip()
        .lower()
    )

    if normalized in AGENT_ROUTES:
        return normalized

    return "unknown"


def normalize_agent_node(
    node: str | None,
) -> str:
    normalized = (
        str(node or "")
        .strip()
        .lower()
    )

    if normalized in AGENT_NODES:
        return normalized

    return "unknown"


def normalize_query_failure_stage(
    stage: str | None,
) -> str:
    normalized = (
        str(stage or "")
        .strip()
        .lower()
    )

    if normalized in QUERY_FAILURE_STAGES:
        return normalized

    return "unknown"


def normalize_safety_outcome(
    outcome: str | None,
) -> str:
    normalized = (
        str(outcome or "")
        .strip()
        .lower()
    )

    if normalized in SAFETY_OUTCOMES:
        return normalized

    return "unknown"


def normalize_safety_category(
    category: str | None,
) -> str:
    normalized = (
        str(category or "")
        .strip()
        .lower()
    )

    if normalized in SAFETY_CATEGORIES:
        return normalized

    return "unknown"


def normalize_provider(
    provider: str | None,
) -> str:
    normalized = (
        str(provider or "")
        .strip()
        .lower()
    )

    if not normalized:
        return "unknown"

    # Provider names originate from application
    # configuration, not user-controlled input.
    #
    # Still enforce a compact normalized value so
    # whitespace/casing differences cannot create
    # unnecessary time series.
    return normalized


# ---------------------------------------------------------
# Agent metrics
# ---------------------------------------------------------

MIRA_AGENT_REQUESTS = Counter(
    "mira_agent_requests_total",
    (
        "Total completed MIRA agent requests "
        "grouped by terminal route."
    ),
    [
        "route",
    ],
)

MIRA_AGENT_DURATION = Histogram(
    "mira_agent_duration_seconds",
    (
        "End-to-end LangGraph agent execution "
        "duration grouped by terminal route."
    ),
    [
        "route",
    ],
    buckets=(
        0.01,
        0.025,
        0.05,
        0.1,
        0.25,
        0.5,
        1.0,
        2.5,
        5.0,
        10.0,
        30.0,
        60.0,
        120.0,
    ),
)

MIRA_AGENT_NODE_DURATION = Histogram(
    "mira_agent_node_duration_seconds",
    (
        "Execution duration for instrumented "
        "LangGraph nodes."
    ),
    [
        "node",
    ],
    buckets=(
        0.001,
        0.005,
        0.01,
        0.025,
        0.05,
        0.1,
        0.25,
        0.5,
        1.0,
        2.5,
        5.0,
        10.0,
        30.0,
        60.0,
        120.0,
    ),
)


# ---------------------------------------------------------
# Safety metrics
# ---------------------------------------------------------

MIRA_SAFETY_GUARD = Counter(
    "mira_safety_guard_total",
    (
        "Total SafetyGuard decisions grouped "
        "by outcome and bounded category."
    ),
    [
        "outcome",
        "category",
    ],
)


# ---------------------------------------------------------
# Query route metrics
# ---------------------------------------------------------

MIRA_QUERY_REQUESTS = Counter(
    "mira_query_requests_total",
    (
        "Total completed query API requests "
        "grouped by final MIRA route."
    ),
    [
        "route",
    ],
)

MIRA_QUERY_DURATION = Histogram(
    "mira_query_duration_seconds",
    (
        "End-to-end query API execution duration "
        "grouped by final MIRA route."
    ),
    [
        "route",
    ],
    buckets=(
        0.01,
        0.025,
        0.05,
        0.1,
        0.25,
        0.5,
        1.0,
        2.5,
        5.0,
        10.0,
        30.0,
        60.0,
        120.0,
    ),
)

MIRA_QUERY_FAILURES = Counter(
    "mira_query_failures_total",
    (
        "Total query API failures grouped by "
        "bounded processing stage."
    ),
    [
        "stage",
    ],
)


# ---------------------------------------------------------
# RAG metrics
# ---------------------------------------------------------

MIRA_RETRIEVAL_DURATION = Histogram(
    "mira_retrieval_duration_seconds",
    (
        "Duration of document retrieval for "
        "RAG requests."
    ),
    buckets=(
        0.001,
        0.005,
        0.01,
        0.025,
        0.05,
        0.1,
        0.25,
        0.5,
        1.0,
        2.5,
        5.0,
        10.0,
    ),
)

MIRA_SELECTED_DOCUMENTS = Histogram(
    "mira_selected_documents",
    (
        "Number of currently selected documents "
        "per MIRA agent request."
    ),
    buckets=(
        0,
        1,
        2,
        3,
        5,
        10,
    ),
)

MIRA_RETRIEVED_CHUNKS = Histogram(
    "mira_retrieved_chunks",
    (
        "Number of raw retrieval results returned "
        "for a RAG request."
    ),
    buckets=(
        0,
        1,
        2,
        3,
        5,
        8,
        10,
        15,
        20,
        30,
        50,
    ),
)


# ---------------------------------------------------------
# LLM metrics
# ---------------------------------------------------------

MIRA_LLM_REQUESTS = Counter(
    "mira_llm_requests_total",
    (
        "Total logical provider runs before "
        "provider-level retries."
    ),
    [
        "provider",
    ],
)

MIRA_LLM_FAILURES = Counter(
    "mira_llm_failures_total",
    (
        "Total provider runs that ultimately "
        "failed after retry handling."
    ),
    [
        "provider",
    ],
)

MIRA_LLM_DURATION = Histogram(
    "mira_llm_duration_seconds",
    (
        "Duration of a complete provider run, "
        "including retries and retry delays."
    ),
    [
        "provider",
    ],
    buckets=(
        0.05,
        0.1,
        0.25,
        0.5,
        1.0,
        2.5,
        5.0,
        10.0,
        20.0,
        30.0,
        60.0,
        120.0,
    ),
)

MIRA_LLM_RETRIES = Counter(
    "mira_llm_retries_total",
    (
        "Total provider retries actually "
        "performed."
    ),
    [
        "provider",
    ],
)

MIRA_LLM_FALLBACKS = Counter(
    "mira_llm_fallback_total",
    (
        "Total LLM provider fallback transitions."
    ),
    [
        "primary_provider",
        "fallback_provider",
    ],
)

# ---------------------------------------------------------
# Ingestion / extraction metrics
# ---------------------------------------------------------

MIRA_INGESTION_DURATION = Histogram(
    "mira_ingestion_duration_seconds",
    "End-to-end document ingestion duration.",
    buckets=(
        0.1,
        0.25,
        0.5,
        1.0,
        2.5,
        5.0,
        10.0,
        30.0,
        60.0,
        120.0,
        300.0,
    ),
)

MIRA_EXTRACTION_DURATION = Histogram(
    "mira_extraction_duration_seconds",
    (
        "End-to-end structured medical "
        "extraction duration."
    ),
    buckets=(
        0.1,
        0.25,
        0.5,
        1.0,
        2.5,
        5.0,
        10.0,
        30.0,
        60.0,
        120.0,
        300.0,
    ),
)

# ---------------------------------------------------------
# Prometheus exposition
# ---------------------------------------------------------

def render_metrics() -> bytes:
    return generate_latest()


def metrics_content_type() -> str:
    return CONTENT_TYPE_LATEST
import logging
from time import perf_counter

from fastapi import (
    APIRouter,
    HTTPException,
    status,
)

from app.api.dependencies.auth import (
    CurrentUser,
)
from app.core.metrics import (
    MIRA_QUERY_DURATION,
    MIRA_QUERY_FAILURES,
    MIRA_QUERY_REQUESTS,
    normalize_agent_route,
    normalize_query_failure_stage,
)
from app.schemas.query import (
    MAX_SELECTED_DOCUMENTS,
    QueryRequest,
    QueryResponse,
)
from app.services.conversation_memory_service import (
    ConversationMemoryService,
)
from app.services.conversation_service import (
    ConversationNotFoundError,
    ConversationService,
)
from app.services.document_service import (
    DocumentService,
)
from app.services.langgraph_agent_service import (
    LangGraphAgentService,
)


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/query",
    tags=["query"],
)


def _record_query_failure(
    stage: str,
) -> None:
    MIRA_QUERY_FAILURES.labels(
        stage=(
            normalize_query_failure_stage(
                stage
            )
        )
    ).inc()


@router.post(
    "",
    response_model=QueryResponse,
    summary="Query owned documents or MIRA",
)
def query_agent(
    request: QueryRequest,
    current_user: CurrentUser,
) -> dict:
    request_started_at = (
        perf_counter()
    )

    selected_ids = (
        request.document_ids
        or []
    )

    # -------------------------------------------------
    # Validate current document selection
    # -------------------------------------------------

    if selected_ids:
        existing_ids = (
            DocumentService
            .get_existing_document_ids(
                document_ids=selected_ids,
                user_id=(
                    current_user.user_id
                ),
            )
        )

        if len(existing_ids) != len(
            selected_ids
        ):
            _record_query_failure(
                "validation"
            )

            # Do not reveal whether a document
            # exists under another account.
            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail=(
                    "One or more selected "
                    "documents were not found."
                ),
            )

    # -------------------------------------------------
    # Load bounded conversation context
    # -------------------------------------------------

    conversation_context: list[
        dict[str, str]
    ] = []

    if request.conversation_id:
        try:
            (
                ConversationService
                .require_owned(
                    conversation_id=(
                        request
                        .conversation_id
                    ),
                    user_id=(
                        current_user
                        .user_id
                    ),
                )
            )

            conversation_context = (
                ConversationService
                .get_context(
                    conversation_id=(
                        request
                        .conversation_id
                    ),
                    user_id=(
                        current_user
                        .user_id
                    ),
                )
            )

        except (
            ConversationNotFoundError
        ) as exc:
            _record_query_failure(
                "conversation_load"
            )

            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail=(
                    "Conversation was "
                    "not found."
                ),
            ) from exc

    # -------------------------------------------------
    # Build retrieval query for vague follow-ups
    # -------------------------------------------------

    retrieval_query = (
        ConversationMemoryService
        .build_retrieval_query(
            query=request.query,
            context=(
                conversation_context
            ),
        )
    )

    # -------------------------------------------------
    # Run MIRA
    # -------------------------------------------------

    try:
        result = (
            LangGraphAgentService
            .query(
                query=request.query,
                document_ids=selected_ids,
                user_id=(
                    current_user.user_id
                ),
                conversation_context=(
                    conversation_context
                ),
                retrieval_query=(
                    retrieval_query
                ),
            )
        )

    except (
        ConversationNotFoundError
    ) as exc:
        _record_query_failure(
            "agent"
        )

        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=(
                "Conversation was "
                "not found."
            ),
        ) from exc

    except Exception as exc:
        _record_query_failure(
            "agent"
        )

        logger.exception(
            (
                "query_service_failed "
                "user_id=%s "
                "selected_count=%s "
                "has_conversation=%s "
                "stage=agent"
            ),
            current_user.user_id,
            len(selected_ids),
            bool(
                request.conversation_id
            ),
        )

        raise HTTPException(
            status_code=(
                status.HTTP_503_SERVICE_UNAVAILABLE
            ),
            detail=(
                "The MIRA query service is "
                "currently unavailable."
            ),
        ) from exc

    # -------------------------------------------------
    # Persist the user + assistant exchange
    # -------------------------------------------------

    try:
        (
            conversation_id,
            message_id,
        ) = (
            ConversationService
            .persist_exchange(
                conversation_id=(
                    request
                    .conversation_id
                ),
                user_id=(
                    current_user
                    .user_id
                ),
                query=request.query,
                result=result,
            )
        )

    except (
        ConversationNotFoundError
    ) as exc:
        _record_query_failure(
            "persistence"
        )

        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=(
                "Conversation was "
                "not found."
            ),
        ) from exc

    except Exception as exc:
        _record_query_failure(
            "persistence"
        )

        logger.exception(
            (
                "query_service_failed "
                "user_id=%s "
                "selected_count=%s "
                "has_conversation=%s "
                "stage=persistence"
            ),
            current_user.user_id,
            len(selected_ids),
            bool(
                request.conversation_id
            ),
        )

        raise HTTPException(
            status_code=(
                status.HTTP_503_SERVICE_UNAVAILABLE
            ),
            detail=(
                "The MIRA query service is "
                "currently unavailable."
            ),
        ) from exc

    # -------------------------------------------------
    # Attach required Batch 9 response metadata
    # -------------------------------------------------

    result["conversation_id"] = (
        conversation_id
    )

    result["message_id"] = (
        message_id
    )

    metric_route = (
        normalize_agent_route(
            result.get(
                "route"
            )
        )
    )

    MIRA_QUERY_REQUESTS.labels(
        route=metric_route
    ).inc()

    MIRA_QUERY_DURATION.labels(
        route=metric_route
    ).observe(
        perf_counter()
        - request_started_at
    )

    return result


__all__ = [
    "MAX_SELECTED_DOCUMENTS",
    "QueryRequest",
    "QueryResponse",
    "query_agent",
    "router",
]
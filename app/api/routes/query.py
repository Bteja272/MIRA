import logging

from fastapi import (
    APIRouter,
    HTTPException,
    status,
)

from app.api.dependencies.auth import (
    CurrentUser,
)
from app.schemas.query import (
    MAX_SELECTED_DOCUMENTS,
    QueryRequest,
    QueryResponse,
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


@router.post(
    "",
    response_model=QueryResponse,
    summary="Query owned documents or MIRA",
)
def query_agent(
    request: QueryRequest,
    current_user: CurrentUser,
) -> dict:
    selected_ids = (
        request.document_ids
        or []
    )

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
            # Do not reveal whether the ID exists
            # under another account.
            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail=(
                    "One or more selected "
                    "documents were not found."
                ),
            )

    try:
        return (
            LangGraphAgentService
            .query(
                query=request.query,
                document_ids=selected_ids,
                user_id=(
                    current_user.user_id
                ),
            )
        )

    except Exception as exc:
        logger.exception(
            (
                "query_service_failed "
                "user_id=%s selected_count=%s"
            ),
            current_user.user_id,
            len(selected_ids),
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


__all__ = [
    "MAX_SELECTED_DOCUMENTS",
    "QueryRequest",
    "QueryResponse",
    "query_agent",
    "router",
]
import logging

from fastapi import (
    APIRouter,
    HTTPException,
    Response,
    status,
)

from app.api.dependencies.auth import (
    CurrentUser,
)
from app.schemas.conversation import (
    ConversationDetailResponse,
    ConversationListResponse,
)
from app.services.conversation_service import (
    ConversationService,
)


logger = logging.getLogger(
    __name__
)


router = APIRouter(
    prefix="/conversations",
    tags=["conversations"],
)


@router.get(
    "",
    response_model=(
        ConversationListResponse
    ),
    summary=(
        "List the authenticated "
        "user's conversations"
    ),
)
def list_conversations(
    current_user: CurrentUser,
) -> dict:
    try:
        conversations = (
            ConversationService
            .list_for_user(
                user_id=(
                    current_user.user_id
                )
            )
        )

        return {
            "conversations": (
                conversations
            ),
        }

    except Exception as exc:
        logger.exception(
            (
                "conversation_list_failed "
                "user_id=%s"
            ),
            current_user.user_id,
        )

        raise HTTPException(
            status_code=(
                status
                .HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "Unable to load "
                "conversations."
            ),
        ) from exc


@router.get(
    "/{conversation_id}",
    response_model=(
        ConversationDetailResponse
    ),
    summary=(
        "Get one owned conversation"
    ),
)
def get_conversation(
    conversation_id: str,
    current_user: CurrentUser,
) -> dict:
    try:
        conversation = (
            ConversationService
            .get_for_user(
                conversation_id=(
                    conversation_id
                ),
                user_id=(
                    current_user.user_id
                ),
            )
        )

    except Exception as exc:
        logger.exception(
            (
                "conversation_read_failed "
                "user_id=%s "
                "conversation_id=%s"
            ),
            current_user.user_id,
            conversation_id,
        )

        raise HTTPException(
            status_code=(
                status
                .HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "Unable to load "
                "conversation."
            ),
        ) from exc

    if conversation is None:
        raise HTTPException(
            status_code=(
                status
                .HTTP_404_NOT_FOUND
            ),
            detail=(
                "Conversation not found."
            ),
        )

    return conversation


@router.delete(
    "/{conversation_id}",
    status_code=(
        status.HTTP_204_NO_CONTENT
    ),
    summary=(
        "Permanently delete one "
        "owned conversation"
    ),
)
def delete_conversation(
    conversation_id: str,
    current_user: CurrentUser,
) -> Response:
    try:
        deleted = (
            ConversationService
            .delete_for_user(
                conversation_id=(
                    conversation_id
                ),
                user_id=(
                    current_user.user_id
                ),
            )
        )

    except Exception as exc:
        logger.exception(
            (
                "conversation_delete_failed "
                "user_id=%s "
                "conversation_id=%s"
            ),
            current_user.user_id,
            conversation_id,
        )

        raise HTTPException(
            status_code=(
                status
                .HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "Unable to delete "
                "conversation."
            ),
        ) from exc

    if not deleted:
        raise HTTPException(
            status_code=(
                status
                .HTTP_404_NOT_FOUND
            ),
            detail=(
                "Conversation not found."
            ),
        )

    return Response(
        status_code=(
            status.HTTP_204_NO_CONTENT
        )
    )
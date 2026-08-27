from fastapi import (
    APIRouter,
    HTTPException,
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


router = APIRouter(
    prefix="/conversations",
    tags=["conversations"],
)


@router.get(
    "",
    response_model=(
        ConversationListResponse
    ),
    summary="List owned conversations",
)
def list_conversations(
    current_user: CurrentUser,
) -> dict:
    return {
        "conversations": (
            ConversationService
            .list_for_user(
                user_id=(
                    current_user.user_id
                )
            )
        )
    }


@router.get(
    "/{conversation_id}",
    response_model=(
        ConversationDetailResponse
    ),
    summary="Read an owned conversation",
)
def get_conversation(
    conversation_id: str,
    current_user: CurrentUser,
) -> dict:
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

    if conversation is None:
        # Intentionally indistinguishable
        # from another user's conversation.
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=(
                "Conversation was not found."
            ),
        )

    return conversation
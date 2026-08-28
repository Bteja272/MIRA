
import unittest
from types import (
    SimpleNamespace,
)
from unittest.mock import (
    patch,
)

from fastapi import (
    HTTPException,
)

from app.api.routes import (
    conversations,
)


class ConversationRouteTests(
    unittest.TestCase
):
    def setUp(self):
        self.user = (
            SimpleNamespace(
                user_id="user-a"
            )
        )

    @patch.object(
        conversations
        .ConversationService,
        "list_for_user",
        return_value=[],
    )
    def test_list_is_user_scoped(
        self,
        list_for_user,
    ):
        result = (
            conversations
            .list_conversations(
                current_user=(
                    self.user
                )
            )
        )

        list_for_user\
            .assert_called_once_with(
                user_id="user-a",
            )

        self.assertEqual(
            result,
            {
                "conversations": [],
            },
        )

    @patch.object(
        conversations
        .ConversationService,
        "get_for_user",
        return_value=None,
    )
    def test_foreign_conversation_is_hidden(
        self,
        get_for_user,
    ):
        with self.assertRaises(
            HTTPException
        ) as context:
            conversations\
                .get_conversation(
                    conversation_id=(
                        "conversation-b"
                    ),
                    current_user=(
                        self.user
                    ),
                )

        self.assertEqual(
            context.exception
            .status_code,
            404,
        )

        get_for_user\
            .assert_called_once_with(
                conversation_id=(
                    "conversation-b"
                ),
                user_id="user-a",
            )

    @patch.object(
        conversations
        .ConversationService,
        "get_for_user",
        return_value={
            "conversation_id": (
                "conversation-a"
            ),
            "title": "Test conversation",
            "created_at": None,
            "updated_at": None,
            "messages": [],
        },
    )
    def test_get_is_user_scoped(
        self,
        get_for_user,
    ):
        result = (
            conversations
            .get_conversation(
                conversation_id=(
                    "conversation-a"
                ),
                current_user=(
                    self.user
                ),
            )
        )

        get_for_user\
            .assert_called_once_with(
                conversation_id=(
                    "conversation-a"
                ),
                user_id="user-a",
            )

        self.assertEqual(
            result[
                "conversation_id"
            ],
            "conversation-a",
        )

    @patch.object(
        conversations
        .ConversationService,
        "delete_for_user",
        return_value=True,
    )
    def test_delete_is_user_scoped(
        self,
        delete_for_user,
    ):
        result = (
            conversations
            .delete_conversation(
                conversation_id=(
                    "conversation-a"
                ),
                current_user=(
                    self.user
                ),
            )
        )

        delete_for_user\
            .assert_called_once_with(
                conversation_id=(
                    "conversation-a"
                ),
                user_id="user-a",
            )

        self.assertEqual(
            result.status_code,
            204,
        )

    @patch.object(
        conversations
        .ConversationService,
        "delete_for_user",
        return_value=False,
    )
    def test_foreign_delete_returns_404(
        self,
        delete_for_user,
    ):
        with self.assertRaises(
            HTTPException
        ) as context:
            conversations\
                .delete_conversation(
                    conversation_id=(
                        "conversation-b"
                    ),
                    current_user=(
                        self.user
                    ),
                )

        self.assertEqual(
            context.exception
            .status_code,
            404,
        )

        delete_for_user\
            .assert_called_once_with(
                conversation_id=(
                    "conversation-b"
                ),
                user_id="user-a",
            )

    @patch.object(
        conversations
        .ConversationService,
        "delete_for_user",
        side_effect=RuntimeError(
            "/private/database/path"
        ),
    )
    def test_delete_hides_internal_error(
        self,
        _delete_for_user,
    ):
        with self.assertRaises(
            HTTPException
        ) as context:
            conversations\
                .delete_conversation(
                    conversation_id=(
                        "conversation-a"
                    ),
                    current_user=(
                        self.user
                    ),
                )

        self.assertEqual(
            context.exception
            .status_code,
            500,
        )

        self.assertNotIn(
            "/private/database/path",
            str(
                context.exception.detail
            ),
        )


if __name__ == "__main__":
    unittest.main()
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import HTTPException

from app.api.routes.query import (
    QueryRequest,
    query_agent,
)
from app.services.conversation_service import (
    ConversationNotFoundError,
)


class QueryForwardingTests(
    unittest.TestCase
):
    @patch(
        "app.api.routes.query."
        "ConversationService."
        "persist_exchange"
    )
    @patch(
        "app.api.routes.query."
        "LangGraphAgentService.query"
    )
    @patch(
        "app.api.routes.query."
        "DocumentService."
        "get_existing_document_ids"
    )
    def test_forwards_user_and_document_ids(
        self,
        mock_existing_ids,
        mock_agent_query,
        mock_persist_exchange,
    ):
        selected_ids = [
            "lab-document",
            "discharge-document",
        ]

        current_user = (
            SimpleNamespace(
                user_id="user-123"
            )
        )

        mock_existing_ids.return_value = (
            selected_ids
        )

        mock_agent_query.return_value = {
            "query": (
                "What are the selected "
                "documents?"
            ),
            "answer": (
                "The selected documents "
                "are available."
            ),
            "route": "rag",
            "document_ids": (
                selected_ids
            ),
            "selected_document_count": 2,
            "sources": [],
        }

        mock_persist_exchange.return_value = (
            "conversation-1",
            "message-1",
        )

        request = QueryRequest(
            query=(
                "What are the selected "
                "documents?"
            ),
            document_ids=(
                selected_ids
            ),
        )

        result = query_agent(
            request=request,
            current_user=current_user,
        )

        mock_existing_ids.assert_called_once_with(
            document_ids=selected_ids,
            user_id="user-123",
        )

        mock_agent_query.assert_called_once_with(
            query=request.query,
            document_ids=selected_ids,
            user_id="user-123",
            conversation_context=[],
            retrieval_query=(
                request.query
            ),
        )

        self.assertEqual(
            mock_persist_exchange.call_args
            .kwargs[
                "conversation_id"
            ],
            None,
        )

        self.assertEqual(
            mock_persist_exchange.call_args
            .kwargs[
                "user_id"
            ],
            "user-123",
        )

        self.assertEqual(
            mock_persist_exchange.call_args
            .kwargs[
                "query"
            ],
            request.query,
        )

        self.assertIs(
            mock_persist_exchange.call_args
            .kwargs[
                "result"
            ],
            mock_agent_query.return_value,
        )

        self.assertEqual(
            result["document_ids"],
            selected_ids,
        )

        self.assertEqual(
            result["conversation_id"],
            "conversation-1",
        )

        self.assertEqual(
            result["message_id"],
            "message-1",
        )

    @patch(
        "app.api.routes.query."
        "ConversationService."
        "persist_exchange"
    )
    @patch(
        "app.api.routes.query."
        "ConversationService."
        "get_context"
    )
    @patch(
        "app.api.routes.query."
        "ConversationService."
        "require_owned"
    )
    @patch(
        "app.api.routes.query."
        "LangGraphAgentService.query"
    )
    @patch(
        "app.api.routes.query."
        "DocumentService."
        "get_existing_document_ids"
    )
    def test_existing_conversation_loads_context(
        self,
        mock_existing_ids,
        mock_agent_query,
        mock_require_owned,
        mock_get_context,
        mock_persist_exchange,
    ):
        selected_ids = [
            "discharge-document",
        ]

        current_user = (
            SimpleNamespace(
                user_id="user-123"
            )
        )

        conversation_context = [
            {
                "role": "user",
                "content": (
                    "What medications "
                    "are listed?"
                ),
            },
            {
                "role": "assistant",
                "content": (
                    "Metformin and "
                    "Lisinopril are listed."
                ),
            },
        ]

        mock_existing_ids.return_value = (
            selected_ids
        )

        mock_get_context.return_value = (
            conversation_context
        )

        mock_agent_query.return_value = {
            "query": (
                "What is the dose of "
                "the first one?"
            ),
            "answer": (
                "The document lists "
                "the requested dosage."
            ),
            "route": "rag",
            "document_ids": (
                selected_ids
            ),
            "selected_document_count": 1,
            "sources": [],
        }

        mock_persist_exchange.return_value = (
            "conversation-1",
            "message-2",
        )

        request = QueryRequest(
            query=(
                "What is the dose of "
                "the first one?"
            ),
            document_ids=(
                selected_ids
            ),
            conversation_id=(
                "conversation-1"
            ),
        )

        result = query_agent(
            request=request,
            current_user=current_user,
        )

        mock_require_owned.assert_called_once_with(
            conversation_id=(
                "conversation-1"
            ),
            user_id="user-123",
        )

        mock_get_context.assert_called_once_with(
            conversation_id=(
                "conversation-1"
            ),
            user_id="user-123",
        )

        agent_kwargs = (
            mock_agent_query
            .call_args.kwargs
        )

        self.assertEqual(
            agent_kwargs[
                "conversation_context"
            ],
            conversation_context,
        )

        self.assertIn(
            "What medications are listed?",
            agent_kwargs[
                "retrieval_query"
            ],
        )

        self.assertIn(
            (
                "What is the dose of "
                "the first one?"
            ),
            agent_kwargs[
                "retrieval_query"
            ],
        )

        self.assertEqual(
            mock_persist_exchange.call_args
            .kwargs[
                "conversation_id"
            ],
            "conversation-1",
        )

        self.assertEqual(
            result["conversation_id"],
            "conversation-1",
        )

        self.assertEqual(
            result["message_id"],
            "message-2",
        )

    @patch(
        "app.api.routes.query."
        "ConversationService."
        "persist_exchange"
    )
    @patch(
        "app.api.routes.query."
        "ConversationService."
        "get_context"
    )
    @patch(
        "app.api.routes.query."
        "ConversationService."
        "require_owned"
    )
    @patch(
        "app.api.routes.query."
        "LangGraphAgentService.query"
    )
    def test_rejects_unowned_conversation(
        self,
        mock_agent_query,
        mock_require_owned,
        mock_get_context,
        mock_persist_exchange,
    ):
        current_user = (
            SimpleNamespace(
                user_id="user-a"
            )
        )

        mock_require_owned.side_effect = (
            ConversationNotFoundError(
                "Conversation not found."
            )
        )

        request = QueryRequest(
            query="Explain that again.",
            conversation_id=(
                "conversation-b"
            ),
        )

        with self.assertRaises(
            HTTPException
        ) as context:
            query_agent(
                request=request,
                current_user=current_user,
            )

        self.assertEqual(
            context.exception.status_code,
            404,
        )

        mock_require_owned.assert_called_once_with(
            conversation_id=(
                "conversation-b"
            ),
            user_id="user-a",
        )

        mock_get_context.assert_not_called()
        mock_agent_query.assert_not_called()
        mock_persist_exchange.assert_not_called()


if __name__ == "__main__":
    unittest.main()
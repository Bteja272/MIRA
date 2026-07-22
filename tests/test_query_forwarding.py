import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app.api.routes.query import (
    QueryRequest,
    query_agent,
)


class QueryForwardingTests(
    unittest.TestCase
):
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
            "route": "rag",
            "document_ids": (
                selected_ids
            ),
            "selected_document_count": 2,
        }

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
        )

        self.assertEqual(
            result["document_ids"],
            selected_ids,
        )


if __name__ == "__main__":
    unittest.main()
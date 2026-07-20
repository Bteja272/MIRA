import unittest
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
    def test_forwards_multiple_document_ids(
        self,
        mock_existing_ids,
        mock_agent_query,
    ):
        selected_ids = [
            "lab-document-id",
            "discharge-document-id",
        ]

        mock_existing_ids.return_value = (
            selected_ids
        )

        mock_agent_query.return_value = {
            "route": "rag",
            "document_ids": selected_ids,
            "selected_document_count": 2,
        }

        request = QueryRequest(
            query=(
                "What are the two selected "
                "documents?"
            ),
            document_ids=selected_ids,
        )

        result = query_agent(
            request
        )

        mock_existing_ids.assert_called_once_with(
            document_ids=selected_ids,
            user_id=None,
        )

        mock_agent_query.assert_called_once_with(
            query=request.query,
            document_ids=selected_ids,
        )

        self.assertEqual(
            result["document_ids"],
            selected_ids,
        )

        self.assertEqual(
            result[
                "selected_document_count"
            ],
            2,
        )


if __name__ == "__main__":
    unittest.main()
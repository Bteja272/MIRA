import unittest
from unittest.mock import patch

from app.services.langgraph_agent_service import (
    AgentState,
    LangGraphAgentService,
)


class LangGraphDocumentStateTests(
    unittest.TestCase
):
    def test_agent_state_declares_document_ids(
        self,
    ):
        self.assertIn(
            "document_ids",
            AgentState.__annotations__,
        )

    @patch(
        "app.services.langgraph_agent_service."
        "RAGService.query"
    )
    def test_real_graph_preserves_document_ids(
        self,
        mock_rag_query,
    ):
        selected_ids = [
            "lab-document-id",
            "discharge-document-id",
        ]

        mock_rag_query.return_value = {
            "answer": "Documents received.",
            "sources": [],
        }

        result = (
            LangGraphAgentService.query(
                query=(
                    "What are the two selected "
                    "documents?"
                ),
                document_ids=selected_ids,
            )
        )

        mock_rag_query.assert_called_once_with(
            query=(
                "What are the two selected "
                "documents?"
            ),
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

        self.assertEqual(
            result["route"],
            "rag",
        )


if __name__ == "__main__":
    unittest.main()
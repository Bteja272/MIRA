import unittest
from unittest.mock import patch

from app.services.langgraph_agent_service import (
    AgentState,
    LangGraphAgentService,
)


class LangGraphUserStateTests(
    unittest.TestCase
):
    def test_state_declares_user_id(
        self,
    ):
        self.assertIn(
            "user_id",
            AgentState.__annotations__,
        )

    @patch(
        "app.services."
        "langgraph_agent_service."
        "_run_safety_guard",
        return_value={
            "allowed": True,
            "category": "allowed",
        },
    )
    @patch(
        "app.services."
        "langgraph_agent_service."
        "RAGService.query"
    )
    def test_graph_forwards_user_id_to_rag(
        self,
        mock_rag_query,
        mock_safety_guard,
    ):
        selected_ids = [
            "lab-document",
            "discharge-document",
        ]

        mock_rag_query.return_value = {
            "answer": "Documents received.",
            "sources": [],
        }

        result = (
            LangGraphAgentService.query(
                query=(
                    "Summarize the "
                    "selected documents."
                ),
                document_ids=(
                    selected_ids
                ),
                user_id="user-123",
            )
        )

        mock_rag_query.assert_called_once_with(
            query=(
                "Summarize the "
                "selected documents."
            ),
            document_ids=(
                selected_ids
            ),
            user_id="user-123",
        )

        self.assertEqual(
            result["route"],
            "rag",
        )


if __name__ == "__main__":
    unittest.main()
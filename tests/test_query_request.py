import unittest

from pydantic import ValidationError

from app.api.routes.query import (
    MAX_SELECTED_DOCUMENTS,
    QueryRequest,
)


class QueryRequestTests(
    unittest.TestCase
):
    def test_accepts_legacy_document_id(
        self,
    ):
        request = QueryRequest(
            query=(
                "Summarize this document."
            ),
            document_id="doc-1",
        )

        self.assertEqual(
            request.document_ids,
            ["doc-1"],
        )

    def test_combines_and_deduplicates_ids(
        self,
    ):
        request = QueryRequest(
            query=(
                "Compare these documents."
            ),
            document_id="doc-1",
            document_ids=[
                "doc-1",
                "doc-2",
                "doc-2",
            ],
        )

        self.assertEqual(
            request.document_ids,
            [
                "doc-1",
                "doc-2",
            ],
        )

    def test_rejects_too_many_documents(
        self,
    ):
        with self.assertRaises(
            ValidationError
        ):
            QueryRequest(
                query=(
                    "Compare everything."
                ),
                document_ids=[
                    f"doc-{index}"
                    for index in range(
                        MAX_SELECTED_DOCUMENTS
                        + 1
                    )
                ],
            )

    def test_strips_query_whitespace(
        self,
    ):
        request = QueryRequest(
            query=(
                "  Provide an overview.  "
            ),
        )

        self.assertEqual(
            request.query,
            "Provide an overview.",
        )

    def test_accepts_conversation_id(
        self,
    ):
        request = QueryRequest(
            query="Explain that again.",
            conversation_id=(
                "conversation-123"
            ),
        )

        self.assertEqual(
            request.conversation_id,
            "conversation-123",
        )

    def test_strips_conversation_id_whitespace(
        self,
    ):
        request = QueryRequest(
            query="Explain that again.",
            conversation_id=(
                "  conversation-123  "
            ),
        )

        self.assertEqual(
            request.conversation_id,
            "conversation-123",
        )

    def test_blank_conversation_id_becomes_none(
        self,
    ):
        request = QueryRequest(
            query="Explain this.",
            conversation_id="   ",
        )

        self.assertIsNone(
            request.conversation_id
        )

    def test_rejects_overlong_conversation_id(
        self,
    ):
        with self.assertRaises(
            ValidationError
        ):
            QueryRequest(
                query="Explain this.",
                conversation_id=(
                    "x" * 37
                ),
            )


if __name__ == "__main__":
    unittest.main()
import unittest
from unittest.mock import patch

from app.services.rag_service import (
    RAGService,
)


class DocumentIdentificationTests(
    unittest.TestCase
):
    @patch(
        "app.services.rag_service."
        "LLMService.generate_response"
    )
    @patch(
        "app.services.rag_service."
        "DocumentService.get_document"
    )
    def test_document_identification_bypasses_llm(
        self,
        mock_get_document,
        mock_generate_response,
    ):
        selected_ids = [
            "lab-document-id",
            "discharge-document-id",
        ]

        mock_get_document.side_effect = [
            {
                "document_id": (
                    selected_ids[0]
                ),
                "filename": (
                    "synthetic_lab_report.txt"
                ),
                "document_type": (
                    "lab_report"
                ),
                "file_size_bytes": 642,
                "chunk_count": 2,
                "uploaded_at": None,
            },
            {
                "document_id": (
                    selected_ids[1]
                ),
                "filename": (
                    "synthetic_discharge_summary.txt"
                ),
                "document_type": (
                    "discharge_summary"
                ),
                "file_size_bytes": 623,
                "chunk_count": 2,
                "uploaded_at": None,
            },
        ]

        result = RAGService.query(
            query=(
                "What are the two "
                "selected documents?"
            ),
            document_ids=selected_ids,
        )

        mock_generate_response.assert_not_called()

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

        self.assertIn(
            "synthetic_lab_report.txt",
            result["answer"],
        )

        self.assertIn(
            (
                "synthetic_discharge_"
                "summary.txt"
            ),
            result["answer"],
        )

        self.assertEqual(
            len(result["sources"]),
            2,
        )

        self.assertEqual(
            result["sources"][0][
                "document_position"
            ],
            1,
        )

        self.assertEqual(
            result["sources"][1][
                "document_position"
            ],
            2,
        )


if __name__ == "__main__":
    unittest.main()
import unittest

from langchain_core.documents import (
    Document,
)

from app.services.prompt_service import (
    PromptService,
)
from app.services.rag_service import (
    RAGService,
)


class MultiDocumentPromptTests(
    unittest.TestCase
):
    def setUp(self):
        self.documents = [
            Document(
                page_content=(
                    "Hemoglobin A1c\n"
                    "Result: 7.2 %\n"
                    "Flag: High"
                ),
                metadata={
                    "document_id": (
                        "doc-1"
                    ),
                    "source": (
                        "lab_report.txt"
                    ),
                    "document_type": (
                        "lab_report"
                    ),
                    "document_position": 1,
                    "chunk_index": 0,
                },
            ),
            Document(
                page_content=(
                    "Discharge Medication\n"
                    "Metformin 500 mg "
                    "twice daily"
                ),
                metadata={
                    "document_id": (
                        "doc-2"
                    ),
                    "source": (
                        "discharge_summary.txt"
                    ),
                    "document_type": (
                        "discharge_summary"
                    ),
                    "document_position": 2,
                    "chunk_index": 0,
                },
            ),
        ]

    def test_comparison_prompt_separates_documents(
        self,
    ):
        prompt = (
            PromptService.build_prompt(
                query=(
                    "Compare these documents."
                ),
                documents=self.documents,
                task="comparison",
            )
        )

        self.assertIn(
            "Cross-document comparison",
            prompt,
        )

        self.assertIn(
            "Document: lab_report.txt",
            prompt,
        )

        self.assertIn(
            (
                "Document: "
                "discharge_summary.txt"
            ),
            prompt,
        )

        self.assertIn(
            "Selected document: 1",
            prompt,
        )

        self.assertIn(
            "Selected document: 2",
            prompt,
        )

    def test_overview_prompt_prohibits_merging(
        self,
    ):
        prompt = (
            PromptService.build_prompt(
                query=(
                    "Give me an overview."
                ),
                documents=self.documents,
                task=(
                    "multi_document_overview"
                ),
            )
        )

        self.assertIn(
            "Combined overview",
            prompt,
        )

        self.assertIn(
            "Do not merge facts",
            prompt,
        )

    def test_detects_comparison_query(
        self,
    ):
        self.assertTrue(
            RAGService
            ._is_comparison_query(
                (
                    "Compare these "
                    "two reports."
                )
            )
        )

    def test_detects_overview_query(
        self,
    ):
        self.assertTrue(
            RAGService
            ._is_summary_query(
                "Provide an overview."
            )
        )


if __name__ == "__main__":
    unittest.main()
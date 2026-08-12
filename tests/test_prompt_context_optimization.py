import unittest

from langchain_core.documents import (
    Document as LangChainDocument,
)

from app.services.prompt_service import (
    PromptService,
)


class PromptContextOptimizationTests(
    unittest.TestCase
):
    def test_prompt_omits_internal_retrieval_metadata(
        self,
    ) -> None:
        document = (
            LangChainDocument(
                page_content=(
                    "HbA1c: 7.2%"
                ),
                metadata={
                    "document_id": "doc-secret",
                    "source": "synthetic.txt",
                    "document_type": (
                        "lab_report"
                    ),
                    "document_position": 1,
                    "page_number": 2,
                    "chunk_index": 4,
                    "similarity_score": 0.991,
                },
            )
        )

        prompt = (
            PromptService.build_prompt(
                query="What is the HbA1c?",
                documents=[
                    document,
                ],
                task="qa",
            )
        )

        self.assertIn(
            "[Source 1]",
            prompt,
        )
        self.assertIn(
            "Document: synthetic.txt",
            prompt,
        )
        self.assertIn(
            "Document type: lab_report",
            prompt,
        )
        self.assertIn(
            "Selected document: 1",
            prompt,
        )
        self.assertIn(
            "Page: 2",
            prompt,
        )

        self.assertNotIn(
            "Document ID:",
            prompt,
        )
        self.assertNotIn(
            "Similarity:",
            prompt,
        )
        self.assertNotIn(
            "Chunk:",
            prompt,
        )
        self.assertNotIn(
            "doc-secret",
            prompt,
        )

    def test_truncation_status_is_exposed_without_altering_source_text(
        self,
    ) -> None:
        document = (
            LangChainDocument(
                page_content=(
                    "Medication: metformin "
                    "500 mg."
                ),
                metadata={
                    "source": "synthetic.txt",
                    "document_type": (
                        "medication_list"
                    ),
                    "context_truncated": True,
                },
            )
        )

        prompt = (
            PromptService.build_prompt(
                query=(
                    "What medication "
                    "is documented?"
                ),
                documents=[
                    document,
                ],
                task="qa",
            )
        )

        self.assertIn(
            (
                "Context status: truncated "
                "to the configured context budget"
            ),
            prompt,
        )
        self.assertIn(
            "Medication: metformin 500 mg.",
            prompt,
        )


if __name__ == "__main__":
    unittest.main()
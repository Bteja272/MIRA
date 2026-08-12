import unittest

from langchain_core.documents import (
    Document as LangChainDocument,
)

from app.services.context_optimization_service import (
    ContextOptimizationService,
)


class ContextOptimizationServiceTests(
    unittest.TestCase
):
    def test_under_budget_preserves_text_exactly(
        self,
    ) -> None:
        original_text = (
            "HbA1c: 7.2%\n"
            "Medication: metformin 500 mg."
        )

        document = (
            LangChainDocument(
                page_content=original_text,
                metadata={
                    "document_id": "doc-1",
                    "source": "synthetic.txt",
                },
            )
        )

        result = (
            ContextOptimizationService
            .optimize(
                documents=[
                    document,
                ],
                token_budget=500,
            )
        )

        self.assertEqual(
            len(result.documents),
            1,
        )
        self.assertEqual(
            result.documents[0]
            .page_content,
            original_text,
        )
        self.assertFalse(
            result.documents[0]
            .metadata[
                "context_truncated"
            ]
        )
        self.assertEqual(
            result.metrics
            .truncated_document_count,
            0,
        )

    def test_over_budget_truncates_without_rewriting_prefix(
        self,
    ) -> None:
        original_text = " ".join(
            f"term{index}"
            for index in range(400)
        )

        document = (
            LangChainDocument(
                page_content=original_text,
                metadata={
                    "document_id": "doc-1",
                },
            )
        )

        result = (
            ContextOptimizationService
            .optimize(
                documents=[
                    document,
                ],
                token_budget=80,
            )
        )

        optimized = (
            result.documents[0]
            .page_content
        )

        self.assertTrue(
            original_text.startswith(
                optimized
            )
        )
        self.assertLessEqual(
            ContextOptimizationService
            .estimate_tokens(
                optimized
            ),
            80,
        )
        self.assertTrue(
            result.documents[0]
            .metadata[
                "context_truncated"
            ]
        )
        self.assertEqual(
            result.metrics
            .truncated_document_count,
            1,
        )

    def test_budget_is_shared_across_documents(
        self,
    ) -> None:
        small_text = (
            "Medication: lisinopril 10 mg."
        )
        large_text = " ".join(
            f"finding{index}"
            for index in range(500)
        )

        result = (
            ContextOptimizationService
            .optimize(
                documents=[
                    LangChainDocument(
                        page_content=small_text,
                        metadata={
                            "document_id": (
                                "doc-small"
                            ),
                        },
                    ),
                    LangChainDocument(
                        page_content=large_text,
                        metadata={
                            "document_id": (
                                "doc-large"
                            ),
                        },
                    ),
                ],
                token_budget=120,
            )
        )

        self.assertEqual(
            len(result.documents),
            2,
        )
        self.assertEqual(
            result.documents[0]
            .page_content,
            small_text,
        )
        self.assertLessEqual(
            result.metrics
            .output_estimated_tokens,
            120,
        )
        self.assertGreater(
            result.metrics
            .truncated_document_count,
            0,
        )


if __name__ == "__main__":
    unittest.main()
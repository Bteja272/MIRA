import unittest

from langchain_core.documents import (
    Document as LangChainDocument,
)

from app.services.rag_service import (
    RAGService,
)


class RAGFocusedFallbackTests(
    unittest.TestCase
):
    def setUp(self):
        self.document = (
            LangChainDocument(
                page_content=(
                    "LABORATORY RESULTS\n"
                    "Hemoglobin A1c\n"
                    "Result: 7.2 %\n"
                    "Reference Range: "
                    "4.0 - 5.6 %\n"
                    "Flag: High\n"
                    "Glucose\n"
                    "Result: 138 mg/dL\n"
                    "Reference Range: "
                    "70 - 99 mg/dL\n"
                    "Flag: High\n"
                    "Total Cholesterol\n"
                    "Result: 196 mg/dL\n"
                    "Reference Range: "
                    "Below 200 mg/dL\n"
                    "Flag: Normal\n"
                ),
                metadata={
                    "source": (
                        "synthetic_lab_"
                        "report.txt"
                    ),
                },
            )
        )

    def test_first_result_returns_only_first_result(
        self,
    ):
        answer = (
            RAGService
            ._build_source_grounded_fallback(
                query=(
                    "What is the value "
                    "of the first result?"
                ),
                documents=[
                    self.document
                ],
                task="qa",
            )
        )

        self.assertIn(
            "Hemoglobin A1c "
            "[Source 1]",
            answer,
        )

        self.assertIn(
            "Result: 7.2 % "
            "[Source 1]",
            answer,
        )

        self.assertNotIn(
            "138 mg/dL",
            answer,
        )

        self.assertNotIn(
            "196 mg/dL",
            answer,
        )

        self.assertNotIn(
            "Reference Range",
            answer,
        )

    def test_second_result_returns_only_second_result(
        self,
    ):
        answer = (
            RAGService
            ._build_source_grounded_fallback(
                query=(
                    "What is the second "
                    "result value?"
                ),
                documents=[
                    self.document
                ],
                task="qa",
            )
        )

        self.assertIn(
            "Glucose [Source 1]",
            answer,
        )

        self.assertIn(
            "Result: 138 mg/dL "
            "[Source 1]",
            answer,
        )

        self.assertNotIn(
            "Result: 7.2 %",
            answer,
        )

        self.assertNotIn(
            "196 mg/dL",
            answer,
        )

    def test_summary_keeps_broad_fallback(
        self,
    ):
        answer = (
            RAGService
            ._build_source_grounded_fallback(
                query=(
                    "Summarize this "
                    "document."
                ),
                documents=[
                    self.document
                ],
                task=(
                    "summarization"
                ),
            )
        )

        self.assertIn(
            (
                "I could not safely "
                "preserve the generated "
                "answer"
            ),
            answer,
        )

        self.assertIn(
            "7.2 %",
            answer,
        )

        self.assertIn(
            "138 mg/dL",
            answer,
        )

        self.assertIn(
            "196 mg/dL",
            answer,
        )

    def test_unresolvable_ordinal_uses_broad_fallback(
        self,
    ):
        answer = (
            RAGService
            ._build_source_grounded_fallback(
                query=(
                    "What is the tenth "
                    "result?"
                ),
                documents=[
                    self.document
                ],
                task="qa",
            )
        )

        self.assertIn(
            (
                "I could not safely "
                "preserve the generated "
                "answer"
            ),
            answer,
        )

        self.assertIn(
            "7.2 %",
            answer,
        )


if __name__ == "__main__":
    unittest.main()
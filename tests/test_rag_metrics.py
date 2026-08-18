import unittest

from evaluation.quality_corpus_loader import (
    RequiredFact,
)
from evaluation.rag_metrics import (
    citation_validity,
    cited_fact_is_supported,
    extract_medical_values,
    fact_is_grounded_in_sources,
    unsupported_medical_values,
)


class RAGMetricTests(
    unittest.TestCase
):
    def test_required_fact_is_supported_by_correct_citation(
        self,
    ) -> None:
        fact = RequiredFact(
            text="7.2 %",
            aliases=[
                "7.2%",
                "7.2 %",
            ],
            source_document_ids=[
                "doc-1",
            ],
        )

        answer = (
            "The documented HbA1c is "
            "7.2 % [Source 1]."
        )

        sources = [
            {
                "source_number": 1,
                "document_id": (
                    "doc-1"
                ),
                "text": (
                    "Hemoglobin A1c: "
                    "7.2 %."
                ),
            }
        ]

        self.assertTrue(
            cited_fact_is_supported(
                answer=answer,
                sources=sources,
                fact=fact,
            )
        )


    def test_grounding_does_not_require_inline_citation(
        self,
    ) -> None:
        fact = RequiredFact(
            text="7.2 %",
            aliases=[
                "7.2%",
                "7.2 %",
            ],
            source_document_ids=[
                "doc-1",
            ],
        )

        self.assertTrue(
            fact_is_grounded_in_sources(
                sources=[
                    {
                        "document_id": "doc-1",
                        "text": "Hemoglobin A1c: 7.2 %.",
                    }
                ],
                fact=fact,
            )
        )

    def test_wrong_source_does_not_support_fact(
        self,
    ) -> None:
        fact = RequiredFact(
            text="40 mg",
            aliases=[
                "40 mg",
            ],
            source_document_ids=[
                "doc-2",
            ],
        )

        answer = (
            "Atorvastatin 40 mg "
            "[Source 1]."
        )

        sources = [
            {
                "source_number": 1,
                "document_id": (
                    "doc-1"
                ),
                "text": (
                    "Atorvastatin "
                    "20 mg."
                ),
            },
            {
                "source_number": 2,
                "document_id": (
                    "doc-2"
                ),
                "text": (
                    "Atorvastatin "
                    "40 mg."
                ),
            },
        ]

        self.assertFalse(
            cited_fact_is_supported(
                answer=answer,
                sources=sources,
                fact=fact,
            )
        )

    def test_invalid_citation_is_counted(
        self,
    ) -> None:
        valid, total = (
            citation_validity(
                answer=(
                    "7.2 % [Source 9]"
                ),
                sources=[
                    {
                        "source_number": 1,
                    }
                ],
            )
        )

        self.assertEqual(
            valid,
            0,
        )
        self.assertEqual(
            total,
            1,
        )

    def test_unsupported_medical_value_is_detected(
        self,
    ) -> None:
        unsupported = (
            unsupported_medical_values(
                answer=(
                    "HbA1c was 9.9 %."
                ),
                sources=[
                    {
                        "text": (
                            "HbA1c: "
                            "7.2 %."
                        )
                    }
                ],
            )
        )

        self.assertEqual(
            unsupported,
            [
                "9.9 %",
            ],
        )

    def test_medical_value_extraction_ignores_source_number(
        self,
    ) -> None:
        values = (
            extract_medical_values(
                "Lisinopril 10 mg "
                "[Source 1]."
            )
        )

        self.assertEqual(
            values,
            [
                "10 mg",
            ],
        )


if __name__ == "__main__":
    unittest.main()
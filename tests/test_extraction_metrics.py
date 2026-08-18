import unittest

from evaluation.extraction_metrics import (
    evaluate_category,
    validate_evidence_refs,
)


class ExtractionMetricTests(
    unittest.TestCase
):
    def test_category_metrics_match_aliases(
        self,
    ) -> None:
        result = evaluate_category(
            category="medications",
            actual_items=[
                {
                    "name": "Lisinopril",
                    "dose": "10 mg",
                    "route": "oral",
                    "frequency": (
                        "daily"
                    ),
                }
            ],
            expected_items=[
                {
                    "name": [
                        "lisinopril",
                    ],
                    "dose": [
                        "10 mg",
                    ],
                    "route": [
                        "by mouth",
                        "oral",
                    ],
                    "frequency": [
                        "once daily",
                        "daily",
                    ],
                }
            ],
        )

        self.assertEqual(
            result[
                "fact_precision"
            ],
            1.0,
        )
        self.assertEqual(
            result[
                "fact_recall"
            ],
            1.0,
        )
        self.assertEqual(
            result[
                "field_precision"
            ],
            1.0,
        )
        self.assertEqual(
            result[
                "field_recall"
            ],
            1.0,
        )

    def test_unexpected_fact_reduces_precision(
        self,
    ) -> None:
        result = evaluate_category(
            category="medications",
            actual_items=[
                {
                    "name": "Metformin",
                    "dose": "500 mg",
                },
                {
                    "name": "Insulin",
                    "dose": "10 units",
                },
            ],
            expected_items=[
                {
                    "name": [
                        "Metformin",
                    ],
                    "dose": [
                        "500 mg",
                    ],
                }
            ],
        )

        self.assertEqual(
            result[
                "fact_recall"
            ],
            1.0,
        )
        self.assertLess(
            result[
                "fact_precision"
            ],
            1.0,
        )

    def test_evidence_reference_is_checked_against_chunk(
        self,
    ) -> None:
        payload = {
            "medications": [
                {
                    "name": "Lisinopril",
                    "sources": [
                        {
                            "document_id": (
                                "doc-1"
                            ),
                            "chunk_id": (
                                "chunk-1"
                            ),
                            "page_number": 1,
                            "chunk_index": 0,
                            "quoted_text": (
                                "Lisinopril "
                                "10 mg"
                            ),
                        }
                    ],
                }
            ]
        }

        result = (
            validate_evidence_refs(
                extraction_payload=(
                    payload
                ),
                document_id="doc-1",
                chunks=[
                    {
                        "chunk_id": (
                            "chunk-1"
                        ),
                        "page_number": 1,
                        "chunk_index": 0,
                        "text": (
                            "Active medication: "
                            "Lisinopril 10 mg."
                        ),
                    }
                ],
            )
        )

        self.assertEqual(
            result[
                "validity_rate"
            ],
            1.0,
        )


if __name__ == "__main__":
    unittest.main()
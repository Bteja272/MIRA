import unittest

from app.services.deterministic_medical_extraction_service import (
    DeterministicMedicalExtractionService,
)


class DeterministicMedicalExtractionRegressionTests(
    unittest.TestCase
):
    def setUp(self) -> None:
        self.document = {
            "document_id": "doc-1",
            "filename": "synthetic.txt",
            "document_type": "lab_report",
        }

    def _chunk(
        self,
        text: str,
    ) -> dict:
        return {
            "chunk_id": "chunk-1",
            "page_number": 1,
            "chunk_index": 0,
            "text": text,
        }

    def test_multiple_labs_on_one_line_are_separated(
        self,
    ) -> None:
        chunk = self._chunk(
            "LDL cholesterol: 118 mg/dL. "
            "HDL cholesterol: 46 mg/dL. "
            "Triglycerides: 162 mg/dL."
        )

        results = (
            DeterministicMedicalExtractionService
            ._extract_lab_results(
                document=self.document,
                chunks=[chunk],
            )
        )

        self.assertEqual(
            [item.test_name for item in results],
            [
                "LDL cholesterol",
                "HDL cholesterol",
                "Triglycerides",
            ],
        )

    def test_lab_heading_does_not_become_test_name(
        self,
    ) -> None:
        chunk = self._chunk(
            "Laboratory Report dated 2026-01-15. "
            "Hemoglobin A1c: 7.2 %. "
            "Documented flag: High. "
            "Reference range: 4.0-5.6 %."
        )

        results = (
            DeterministicMedicalExtractionService
            ._extract_lab_results(
                document=self.document,
                chunks=[chunk],
            )
        )

        self.assertEqual(
            len(results),
            1,
        )
        self.assertEqual(
            results[0].test_name,
            "Hemoglobin A1c",
        )
        self.assertEqual(
            results[0].unit,
            "%",
        )
        self.assertEqual(
            results[0].reference_range,
            "4.0-5.6 %",
        )
        self.assertEqual(
            results[0].flag.value,
            "high",
        )

    def test_reconciliation_sentence_extracts_all_medications(
        self,
    ) -> None:
        document = {
            **self.document,
            "document_type": (
                "discharge_summary"
            ),
        }
        chunk = self._chunk(
            "Medication reconciliation lists "
            "metformin 500 mg twice daily, "
            "lisinopril 10 mg once daily, and "
            "atorvastatin 20 mg nightly."
        )

        medications = (
            DeterministicMedicalExtractionService
            ._extract_medications(
                document=document,
                chunks=[chunk],
            )
        )

        self.assertEqual(
            [
                (
                    item.name.casefold(),
                    item.dose.casefold(),
                    item.frequency,
                )
                for item in medications
            ],
            [
                (
                    "metformin",
                    "500 mg",
                    "twice daily",
                ),
                (
                    "lisinopril",
                    "10 mg",
                    "once daily",
                ),
                (
                    "atorvastatin",
                    "20 mg",
                    "nightly",
                ),
            ],
        )


if __name__ == "__main__":
    unittest.main()
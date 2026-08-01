import unittest

from app.services.deterministic_medical_extraction_service import (
    DeterministicMedicalExtractionService,
)


class DeterministicMedicalExtractionHardeningTests(
    unittest.TestCase
):
    def test_reference_range_line_is_not_extracted_as_lab_result(
        self,
    ) -> None:
        document = {
            "document_id": "document-123",
            "filename": "synthetic_lab_report.txt",
            "document_type": "lab_report",
        }
        chunks = [
            {
                "chunk_id": "chunk-123",
                "document_id": "document-123",
                "page_number": 1,
                "chunk_index": 0,
                "text": (
                    "Hemoglobin: 13.8 g/dL\n"
                    "Reference range: 12.0-16.0 g/dL"
                ),
            }
        ]

        extraction = (
            DeterministicMedicalExtractionService
            .extract(
                document=document,
                chunks=chunks,
            )
        )

        self.assertEqual(
            len(extraction.lab_results),
            1,
        )
        self.assertEqual(
            extraction.lab_results[0].test_name,
            "Hemoglobin",
        )


if __name__ == "__main__":
    unittest.main()
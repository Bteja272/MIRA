import json
import unittest
from unittest.mock import patch

from app.schemas.medical_extraction import (
    ExtractionMethod,
)
from app.services.medical_extraction_service import (
    MedicalExtractionService,
)


class HybridMedicalExtractionTests(
    unittest.TestCase
):
    @patch(
        "app.services.medical_extraction_service."
        "LLMService.generate_response"
    )
    @patch.object(
        MedicalExtractionService,
        "_load_document_context",
    )
    def test_deterministic_result_is_merged_with_candidate_facts(
        self,
        mock_load_context,
        mock_generate_response,
    ) -> None:
        document = {
            "document_id": "document-123",
            "filename": (
                "synthetic_lab_report.txt"
            ),
            "document_type": "lab_report",
        }

        chunks = [
            {
                "chunk_id": "chunk-1",
                "document_id": "document-123",
                "page_number": 1,
                "chunk_index": 0,
                "text": (
                    "Patient Name: "
                    "Synthetic Patient\n"
                    "Provider: Dr. Example\n"
                    "Hemoglobin: 13.8 g/dL"
                ),
            }
        ]

        mock_load_context.return_value = (
            document,
            chunks,
        )

        mock_generate_response.return_value = (
            json.dumps(
                {
                    "patient": {},
                    "document_date": None,
                    "providers": [
                        {
                            "name": "Dr. Example",
                            "role": None,
                            "organization": None,
                        }
                    ],
                    "diagnoses": [],
                    "medications": [],
                    "lab_results": [],
                    "procedures": [],
                    "follow_up_instructions": [],
                }
            )
        )

        extraction = MedicalExtractionService.extract(
            document_id="document-123",
            user_id="user-123",
        )

        self.assertEqual(
            extraction.patient.name.value,
            "Synthetic Patient",
        )
        self.assertEqual(
            len(extraction.lab_results),
            1,
        )
        self.assertEqual(
            extraction.lab_results[0].test_name,
            "Hemoglobin",
        )
        self.assertEqual(
            extraction.lab_results[0].extraction_method,
            ExtractionMethod.DETERMINISTIC,
        )
        self.assertEqual(
            extraction.providers[0].name,
            "Dr. Example",
        )
        self.assertEqual(
            extraction.providers[0].extraction_method,
            ExtractionMethod.LLM,
        )


if __name__ == "__main__":
    unittest.main()
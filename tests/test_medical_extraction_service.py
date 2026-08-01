import json
import unittest
from unittest.mock import patch

from app.schemas.medical_extraction import (
    ExtractionMethod,
    ExtractionStatus,
    LabResultFlag,
    MedicalDocumentType,
)
from app.services.medical_extraction_service import (
    MedicalExtractionContentTooLargeError,
    MedicalExtractionNotFoundError,
    MedicalExtractionService,
    MedicalExtractionValidationError,
)


class MedicalExtractionServiceTests(
    unittest.TestCase
):
    def setUp(self) -> None:
        self.document = {
            "document_id": "document-123",
            "filename": (
                "synthetic_lab_report.txt"
            ),
            "document_type": "lab_report",
        }

        self.chunks = [
            {
                "chunk_id": "chunk-123",
                "document_id": "document-123",
                "page_number": 1,
                "chunk_index": 0,
                "text": (
                    "Patient: Synthetic Patient\n"
                    "Report Date: 2026-04-04\n"
                    "Provider: Dr. Example\n"
                    "Diagnosis: Mild anemia\n"
                    "Hemoglobin: 13.8 g/dL\n"
                    "Reference range: "
                    "12.0-16.0 g/dL"
                ),
            }
        ]

    @staticmethod
    def _valid_candidate_response() -> str:
        return json.dumps(
            {
                "patient": {
                    "name": "Synthetic Patient",
                    "date_of_birth": None,
                    "medical_record_number": None,
                },
                "document_date": "2026-04-04",
                "providers": [
                    {
                        "name": "Dr. Example",
                        "role": None,
                        "organization": None,
                    }
                ],
                "diagnoses": [
                    {
                        "name": "Mild anemia",
                        "code": None,
                        "code_system": None,
                        "status": "unknown",
                    }
                ],
                "medications": [],
                "lab_results": [],
                "procedures": [],
                "follow_up_instructions": [],
            }
        )

    @patch(
        "app.services.medical_extraction_service."
        "LLMService.generate_response"
    )
    @patch.object(
        MedicalExtractionService,
        "_load_document_context",
    )
    def test_valid_candidate_is_enriched_and_merged(
        self,
        mock_load_context,
        mock_generate_response,
    ) -> None:
        mock_load_context.return_value = (
            self.document,
            self.chunks,
        )
        mock_generate_response.return_value = (
            self._valid_candidate_response()
        )

        extraction = MedicalExtractionService.extract(
            document_id="document-123",
            user_id="user-123",
        )

        self.assertEqual(
            extraction.document_id,
            "document-123",
        )
        self.assertEqual(
            extraction.document_type,
            MedicalDocumentType.LAB_REPORT,
        )

        # Patient name and lab result are retained from the
        # deterministic path.
        self.assertEqual(
            extraction.patient.name.value,
            "Synthetic Patient",
        )
        self.assertEqual(
            extraction.patient.name.extraction_method,
            ExtractionMethod.DETERMINISTIC,
        )
        self.assertEqual(
            extraction.lab_results[0].test_name,
            "Hemoglobin",
        )
        self.assertEqual(
            extraction.lab_results[0].flag,
            LabResultFlag.UNKNOWN,
        )

        # Contextual facts are created by the server from the
        # lightweight LLM candidate.
        self.assertEqual(
            extraction.providers[0].name,
            "Dr. Example",
        )
        self.assertEqual(
            extraction.providers[0].extraction_method,
            ExtractionMethod.LLM,
        )

        source = extraction.providers[0].sources[0]
        self.assertEqual(
            source.document_id,
            "document-123",
        )
        self.assertEqual(
            source.chunk_id,
            "chunk-123",
        )
        self.assertEqual(
            source.source_filename,
            "synthetic_lab_report.txt",
        )
        self.assertEqual(source.page_number, 1)
        self.assertEqual(source.chunk_index, 0)
        self.assertEqual(
            source.quoted_text,
            "Provider: Dr. Example",
        )

        mock_generate_response.assert_called_once()

    @patch(
        "app.services.medical_extraction_service."
        "LLMService.generate_response"
    )
    @patch.object(
        MedicalExtractionService,
        "_load_document_context",
    )
    def test_invalid_json_is_repaired_once(
        self,
        mock_load_context,
        mock_generate_response,
    ) -> None:
        mock_load_context.return_value = (
            self.document,
            self.chunks,
        )
        mock_generate_response.side_effect = [
            "This is not valid JSON.",
            self._valid_candidate_response(),
        ]

        extraction = MedicalExtractionService.extract(
            document_id="document-123",
            user_id="user-123",
        )

        self.assertEqual(
            extraction.document_id,
            "document-123",
        )
        self.assertEqual(
            mock_generate_response.call_count,
            2,
        )

    @patch(
        "app.services.medical_extraction_service."
        "LLMService.generate_response"
    )
    @patch.object(
        MedicalExtractionService,
        "_load_document_context",
    )
    def test_markdown_json_fence_is_accepted(
        self,
        mock_load_context,
        mock_generate_response,
    ) -> None:
        mock_load_context.return_value = (
            self.document,
            self.chunks,
        )
        mock_generate_response.return_value = (
            "```json\n"
            + self._valid_candidate_response()
            + "\n```"
        )

        extraction = MedicalExtractionService.extract(
            document_id="document-123",
            user_id="user-123",
        )

        self.assertEqual(
            extraction.document_id,
            "document-123",
        )

    @patch(
        "app.services.medical_extraction_service."
        "LLMService.generate_response"
    )
    @patch.object(
        MedicalExtractionService,
        "_load_document_context",
    )
    def test_unverifiable_candidate_is_removed_without_repair(
        self,
        mock_load_context,
        mock_generate_response,
    ) -> None:
        mock_load_context.return_value = (
            self.document,
            self.chunks,
        )

        invalid_response = json.dumps(
            {
                "patient": {},
                "providers": [],
                "diagnoses": [],
                "medications": [],
                "lab_results": [
                    {
                        "test_name": "Glucose",
                        "raw_value": "500",
                        "unit": "mg/dL",
                        "reference_range": None,
                        "flag": "critical",
                        "collected_at": None,
                    }
                ],
                "procedures": [],
                "follow_up_instructions": [],
            }
        )

        mock_generate_response.return_value = (
            invalid_response
        )

        extraction = MedicalExtractionService.extract(
            document_id="document-123",
            user_id="user-123",
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
            mock_generate_response.call_count,
            1,
        )
        self.assertTrue(
            any(
                warning.code
                == "unsupported_candidate_facts_removed"
                for warning in extraction.warnings
            )
        )


    @patch(
        "app.services.medical_extraction_service."
        "LLMService.generate_response"
    )
    @patch.object(
        MedicalExtractionService,
        "_load_document_context",
    )
    def test_unsupported_optional_field_is_removed(
        self,
        mock_load_context,
        mock_generate_response,
    ) -> None:
        mock_load_context.return_value = (
            self.document,
            self.chunks,
        )
        mock_generate_response.return_value = (
            json.dumps(
                {
                    "patient": {},
                    "providers": [
                        {
                            "name": "Dr. Example",
                            "role": None,
                            "organization": "Invented Clinic",
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

        self.assertIsNone(
            extraction.providers[0].organization
        )
        self.assertTrue(
            any(
                warning.code
                == "unsupported_candidate_fields_removed"
                for warning in extraction.warnings
            )
        )
        self.assertEqual(
            mock_generate_response.call_count,
            1,
        )

    @patch.object(
        MedicalExtractionService,
        "_load_document_context",
    )
    def test_large_document_is_rejected(
        self,
        mock_load_context,
    ) -> None:
        large_chunks = [
            {
                "chunk_id": "chunk-large",
                "document_id": "document-123",
                "page_number": 1,
                "chunk_index": 0,
                "text": (
                    "x"
                    * (
                        MedicalExtractionService
                        .MAX_DOCUMENT_CHARACTERS
                        + 1
                    )
                ),
            }
        ]

        mock_load_context.return_value = (
            self.document,
            large_chunks,
        )

        with self.assertRaises(
            MedicalExtractionContentTooLargeError
        ):
            MedicalExtractionService.extract(
                document_id="document-123",
                user_id="user-123",
            )

    @patch(
        "app.services.medical_extraction_service."
        "MedicalExtractionService._load_document_context",
        side_effect=MedicalExtractionNotFoundError(
            "Document not found."
        ),
    )
    def test_unowned_document_is_not_found(
        self,
        mock_load_document_context,
    ) -> None:
        with self.assertRaises(
            MedicalExtractionNotFoundError
        ):
            MedicalExtractionService.extract(
                document_id=(
                    "another-users-document"
                ),
                user_id="user-123",
            )

        mock_load_document_context.assert_called_once_with(
            document_id=(
                "another-users-document"
            ),
            user_id="user-123",
        )

    @patch(
        "app.services.medical_extraction_service."
        "LLMService.generate_response"
    )
    @patch.object(
        MedicalExtractionService,
        "_load_document_context",
    )
    def test_unknown_document_type_falls_back_safely(
        self,
        mock_load_context,
        mock_generate_response,
    ) -> None:
        unknown_document = {
            **self.document,
            "document_type": "unexpected_type",
        }

        mock_load_context.return_value = (
            unknown_document,
            self.chunks,
        )
        mock_generate_response.return_value = (
            self._valid_candidate_response()
        )

        extraction = MedicalExtractionService.extract(
            document_id="document-123",
            user_id="user-123",
        )

        self.assertEqual(
            extraction.document_type,
            MedicalDocumentType.UNKNOWN,
        )

    @patch(
        "app.services.medical_extraction_service."
        "LLMService.generate_response",
        side_effect=RuntimeError(
            "Ollama unavailable"
        ),
    )
    @patch.object(
        MedicalExtractionService,
        "_load_document_context",
    )
    def test_first_llm_transport_failure_uses_deterministic_fallback(
        self,
        mock_load_context,
        _mock_generate_response,
    ) -> None:
        mock_load_context.return_value = (
            self.document,
            self.chunks,
        )

        extraction = MedicalExtractionService.extract(
            document_id="document-123",
            user_id="user-123",
        )

        self.assertEqual(
            extraction.status,
            ExtractionStatus.PARTIAL,
        )
        self.assertTrue(
            any(
                warning.code
                == "contextual_extraction_unavailable"
                for warning in extraction.warnings
            )
        )


if __name__ == "__main__":
    unittest.main()
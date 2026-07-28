import unittest
from datetime import date

from pydantic import ValidationError

from app.schemas.medical_extraction import (
    ExtractionMethod,
    LabResultFlag,
    LabResultInformation,
    MedicalDocumentExtraction,
    MedicalDocumentType,
    MedicationInformation,
    MedicationStatus,
    PatientInformation,
    SourceEvidence,
    SourcedDateValue,
    SourcedTextValue,
)


class MedicalExtractionSchemaTests(
    unittest.TestCase
):
    def setUp(self) -> None:
        self.document_id = (
            "document-123"
        )

        self.source = SourceEvidence(
            document_id=self.document_id,
            chunk_id="chunk-456",
            source_filename=(
                "synthetic_lab_report.txt"
            ),
            page_number=1,
            chunk_index=0,
            quoted_text=(
                "Hemoglobin: 13.8 g/dL "
                "Reference range: "
                "12.0-16.0 g/dL"
            ),
        )

    def test_valid_extraction(
        self,
    ) -> None:
        extraction = (
            MedicalDocumentExtraction(
                document_id=(
                    self.document_id
                ),
                document_type=(
                    MedicalDocumentType
                    .LAB_REPORT
                ),
                patient=(
                    PatientInformation(
                        name=(
                            SourcedTextValue(
                                value=(
                                    "Synthetic Patient"
                                ),
                                confidence=0.99,
                                extraction_method=(
                                    ExtractionMethod
                                    .DETERMINISTIC
                                ),
                                sources=[
                                    self.source
                                ],
                            )
                        ),
                        date_of_birth=(
                            SourcedDateValue(
                                raw_value=(
                                    "January 1, 1990"
                                ),
                                normalized_value=(
                                    date(
                                        1990,
                                        1,
                                        1,
                                    )
                                ),
                                confidence=0.95,
                                extraction_method=(
                                    ExtractionMethod
                                    .HYBRID
                                ),
                                sources=[
                                    self.source
                                ],
                            )
                        ),
                    )
                ),
                lab_results=[
                    LabResultInformation(
                        test_name=(
                            "Hemoglobin"
                        ),
                        raw_value="13.8",
                        numeric_value=13.8,
                        unit="g/dL",
                        reference_range=(
                            "12.0-16.0 g/dL"
                        ),
                        flag=(
                            LabResultFlag
                            .NORMAL
                        ),
                        confidence=0.98,
                        extraction_method=(
                            ExtractionMethod
                            .DETERMINISTIC
                        ),
                        sources=[
                            self.source
                        ],
                    )
                ],
                medications=[
                    MedicationInformation(
                        name="Aspirin",
                        dose="81 mg",
                        frequency=(
                            "once daily"
                        ),
                        status=(
                            MedicationStatus
                            .CURRENT
                        ),
                        confidence=0.90,
                        extraction_method=(
                            ExtractionMethod
                            .LLM
                        ),
                        sources=[
                            self.source
                        ],
                    )
                ],
                extraction_confidence=0.96,
            )
        )

        self.assertEqual(
            extraction.document_id,
            self.document_id,
        )

        self.assertEqual(
            len(
                extraction.lab_results
            ),
            1,
        )

        self.assertEqual(
            extraction.lab_results[
                0
            ].test_name,
            "Hemoglobin",
        )

    def test_confidence_must_be_between_zero_and_one(
        self,
    ) -> None:
        with self.assertRaises(
            ValidationError
        ):
            MedicalDocumentExtraction(
                document_id=(
                    self.document_id
                ),
                document_type=(
                    MedicalDocumentType
                    .LAB_REPORT
                ),
                extraction_confidence=1.5,
            )

    def test_extracted_fact_requires_evidence(
        self,
    ) -> None:
        with self.assertRaises(
            ValidationError
        ):
            MedicalDocumentExtraction(
                document_id=(
                    self.document_id
                ),
                document_type=(
                    MedicalDocumentType
                    .LAB_REPORT
                ),
                lab_results=[
                    {
                        "test_name": (
                            "Glucose"
                        ),
                        "raw_value": "110",
                        "unit": "mg/dL",
                        "confidence": 0.9,
                        "extraction_method": (
                            "deterministic"
                        ),
                        "sources": [],
                    }
                ],
                extraction_confidence=0.9,
            )

    def test_source_must_match_document(
        self,
    ) -> None:
        incorrect_source = (
            SourceEvidence(
                document_id=(
                    "another-document"
                ),
                chunk_id="chunk-789",
                page_number=1,
                chunk_index=0,
                quoted_text=(
                    "Glucose 110 mg/dL"
                ),
            )
        )

        with self.assertRaises(
            ValidationError
        ):
            MedicalDocumentExtraction(
                document_id=(
                    self.document_id
                ),
                document_type=(
                    MedicalDocumentType
                    .LAB_REPORT
                ),
                lab_results=[
                    LabResultInformation(
                        test_name="Glucose",
                        raw_value="110",
                        numeric_value=110,
                        unit="mg/dL",
                        flag=(
                            LabResultFlag
                            .HIGH
                        ),
                        confidence=0.9,
                        extraction_method=(
                            ExtractionMethod
                            .DETERMINISTIC
                        ),
                        sources=[
                            incorrect_source
                        ],
                    )
                ],
                extraction_confidence=0.9,
            )

    def test_unknown_fields_are_rejected(
        self,
    ) -> None:
        with self.assertRaises(
            ValidationError
        ):
            MedicalDocumentExtraction(
                document_id=(
                    self.document_id
                ),
                document_type=(
                    MedicalDocumentType
                    .LAB_REPORT
                ),
                extraction_confidence=0.9,
                fabricated_field=(
                    "not allowed"
                ),
            )

    def test_missing_information_can_remain_empty(
        self,
    ) -> None:
        extraction = (
            MedicalDocumentExtraction(
                document_id=(
                    self.document_id
                ),
                document_type=(
                    MedicalDocumentType
                    .UNKNOWN
                ),
                extraction_confidence=0.0,
            )
        )

        self.assertEqual(
            extraction.diagnoses,
            [],
        )

        self.assertEqual(
            extraction.medications,
            [],
        )

        self.assertEqual(
            extraction.lab_results,
            [],
        )

        self.assertIsNone(
            extraction.patient.name
        )

    def test_json_serialization(
        self,
    ) -> None:
        extraction = (
            MedicalDocumentExtraction(
                document_id=(
                    self.document_id
                ),
                document_type=(
                    MedicalDocumentType
                    .UNKNOWN
                ),
                extraction_confidence=0.0,
            )
        )

        serialized = (
            extraction.model_dump(
                mode="json"
            )
        )

        self.assertEqual(
            serialized[
                "schema_version"
            ],
            "1.0",
        )

        self.assertEqual(
            serialized[
                "document_type"
            ],
            "unknown",
        )

        self.assertIn(
            "generated_at",
            serialized,
        )


if __name__ == "__main__":
    unittest.main()
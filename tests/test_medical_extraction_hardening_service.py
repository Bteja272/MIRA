import unittest

from app.schemas.medical_extraction import (
    DiagnosisInformation,
    ExtractionMethod,
    ExtractionStatus,
    LabResultFlag,
    LabResultInformation,
    MedicalDocumentExtraction,
    MedicalDocumentType,
    MedicationInformation,
    PatientInformation,
    ProviderInformation,
    SourceEvidence,
    SourcedTextValue,
)
from app.services.medical_extraction_hardening_service import (
    MedicalExtractionHardeningError,
    MedicalExtractionHardeningService,
)


class MedicalExtractionHardeningServiceTests(
    unittest.TestCase
):
    def setUp(self) -> None:
        self.document_id = "document-123"
        self.chunk_id = "chunk-123"

    def _source(
        self,
        quoted_text: str,
    ) -> SourceEvidence:
        return SourceEvidence(
            document_id=self.document_id,
            chunk_id=self.chunk_id,
            source_filename="synthetic.txt",
            page_number=1,
            chunk_index=0,
            quoted_text=quoted_text,
        )

    def test_aggregate_confidence_uses_all_facts(
        self,
    ) -> None:
        extraction = MedicalDocumentExtraction(
            document_id=self.document_id,
            document_type=(
                MedicalDocumentType
                .DISCHARGE_SUMMARY
            ),
            status=ExtractionStatus.COMPLETED,
            patient=PatientInformation(
                name=SourcedTextValue(
                    value="Test Patient",
                    confidence=0.99,
                    extraction_method=(
                        ExtractionMethod
                        .DETERMINISTIC
                    ),
                    sources=[
                        self._source(
                            "Patient: Test Patient"
                        )
                    ],
                )
            ),
            providers=[
                ProviderInformation(
                    name="Dr. Example",
                    role=None,
                    organization=None,
                    confidence=0.88,
                    extraction_method=(
                        ExtractionMethod.LLM
                    ),
                    sources=[
                        self._source(
                            "Attending Physician: Dr. Example"
                        )
                    ],
                )
            ],
            diagnoses=[
                DiagnosisInformation(
                    name="Hypertension",
                    confidence=0.86,
                    extraction_method=(
                        ExtractionMethod.LLM
                    ),
                    sources=[
                        self._source(
                            "Diagnosis: Hypertension"
                        )
                    ],
                )
            ],
            medications=[
                MedicationInformation(
                    name="Metformin",
                    dose="500 mg",
                    route="oral",
                    frequency="twice daily",
                    confidence=0.88,
                    extraction_method=(
                        ExtractionMethod.LLM
                    ),
                    sources=[
                        self._source(
                            "Metformin 500 mg by mouth twice daily."
                        )
                    ],
                )
            ],
            extraction_confidence=0.99,
        )

        hardened = (
            MedicalExtractionHardeningService
            .finalize(extraction)
        )

        self.assertEqual(
            hardened.extraction_confidence,
            0.902,
        )
        self.assertEqual(
            hardened.status,
            ExtractionStatus.COMPLETED,
        )

    def test_duplicate_medication_is_removed(
        self,
    ) -> None:
        medication = MedicationInformation(
            name="Metformin",
            dose="500 mg",
            route="by mouth",
            frequency="twice daily",
            confidence=0.88,
            extraction_method=(
                ExtractionMethod.LLM
            ),
            sources=[
                self._source(
                    "Metformin 500 mg by mouth twice daily."
                )
            ],
        )

        extraction = MedicalDocumentExtraction(
            document_id=self.document_id,
            document_type=(
                MedicalDocumentType
                .DISCHARGE_SUMMARY
            ),
            medications=[
                medication,
                medication.model_copy(),
            ],
            extraction_confidence=0.88,
        )

        hardened = (
            MedicalExtractionHardeningService
            .finalize(extraction)
        )

        self.assertEqual(
            len(hardened.medications),
            1,
        )
        self.assertEqual(
            hardened.status,
            ExtractionStatus.PARTIAL,
        )
        self.assertTrue(
            any(
                warning.code
                == "duplicate_facts_removed"
                for warning in hardened.warnings
            )
        )

    def test_unsupported_lab_flag_is_rejected(
        self,
    ) -> None:
        extraction = MedicalDocumentExtraction(
            document_id=self.document_id,
            document_type=(
                MedicalDocumentType.LAB_REPORT
            ),
            lab_results=[
                LabResultInformation(
                    test_name="Glucose",
                    raw_value="110",
                    unit="mg/dL",
                    flag=LabResultFlag.CRITICAL,
                    confidence=0.90,
                    extraction_method=(
                        ExtractionMethod.LLM
                    ),
                    sources=[
                        self._source(
                            "Glucose: 110 mg/dL"
                        )
                    ],
                )
            ],
            extraction_confidence=0.90,
        )

        with self.assertRaises(
            MedicalExtractionHardeningError
        ):
            (
                MedicalExtractionHardeningService
                .finalize(extraction)
            )


if __name__ == "__main__":
    unittest.main()
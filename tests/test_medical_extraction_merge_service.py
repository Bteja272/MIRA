import unittest

from app.schemas.medical_extraction import (
    ExtractionMethod,
    LabResultInformation,
    MedicalDocumentExtraction,
    MedicalDocumentType,
    PatientInformation,
    SourceEvidence,
    SourcedTextValue,
)
from app.services.medical_extraction_merge_service import (
    MedicalExtractionMergeService,
)


class MedicalExtractionMergeTests(
    unittest.TestCase
):
    def setUp(self) -> None:
        self.source = SourceEvidence(
            document_id="document-123",
            chunk_id="chunk-1",
            source_filename=(
                "synthetic.txt"
            ),
            page_number=1,
            chunk_index=0,
            quoted_text=(
                "Hemoglobin: 13.8 g/dL"
            ),
        )

    def _lab(
        self,
        test_name: str,
        raw_value: str,
        method: ExtractionMethod,
    ) -> LabResultInformation:
        return LabResultInformation(
            test_name=test_name,
            raw_value=raw_value,
            numeric_value=float(
                raw_value
            ),
            unit="g/dL",
            confidence=0.95,
            extraction_method=method,
            sources=[self.source],
        )

    def test_deterministic_duplicate_wins(
        self,
    ) -> None:
        deterministic_lab = self._lab(
            "Hemoglobin",
            "13.8",
            (
                ExtractionMethod
                .DETERMINISTIC
            ),
        )

        llm_lab = self._lab(
            "Hemoglobin",
            "13.8",
            ExtractionMethod.LLM,
        )

        deterministic = (
            MedicalDocumentExtraction(
                document_id=(
                    "document-123"
                ),
                document_type=(
                    MedicalDocumentType
                    .LAB_REPORT
                ),
                lab_results=[
                    deterministic_lab
                ],
                extraction_confidence=0.98,
            )
        )

        llm = (
            MedicalDocumentExtraction(
                document_id=(
                    "document-123"
                ),
                document_type=(
                    MedicalDocumentType
                    .LAB_REPORT
                ),
                lab_results=[
                    llm_lab
                ],
                extraction_confidence=0.90,
            )
        )

        merged = (
            MedicalExtractionMergeService
            .merge(
                deterministic=(
                    deterministic
                ),
                llm=llm,
            )
        )

        self.assertEqual(
            len(merged.lab_results),
            1,
        )

        self.assertEqual(
            merged.lab_results[
                0
            ].extraction_method,
            (
                ExtractionMethod
                .DETERMINISTIC
            ),
        )

    def test_unique_llm_fact_is_preserved(
        self,
    ) -> None:
        deterministic = (
            MedicalDocumentExtraction(
                document_id=(
                    "document-123"
                ),
                document_type=(
                    MedicalDocumentType
                    .LAB_REPORT
                ),
                lab_results=[
                    self._lab(
                        "Hemoglobin",
                        "13.8",
                        ExtractionMethod
                        .DETERMINISTIC,
                    )
                ],
                extraction_confidence=0.98,
            )
        )

        llm = (
            MedicalDocumentExtraction(
                document_id=(
                    "document-123"
                ),
                document_type=(
                    MedicalDocumentType
                    .LAB_REPORT
                ),
                lab_results=[
                    self._lab(
                        "Ferritin",
                        "45",
                        ExtractionMethod.LLM,
                    )
                ],
                extraction_confidence=0.90,
            )
        )

        merged = (
            MedicalExtractionMergeService
            .merge(
                deterministic=(
                    deterministic
                ),
                llm=llm,
            )
        )

        self.assertEqual(
            len(merged.lab_results),
            2,
        )

    def test_deterministic_patient_name_wins(
        self,
    ) -> None:
        deterministic = (
            MedicalDocumentExtraction(
                document_id=(
                    "document-123"
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
                        )
                    )
                ),
                extraction_confidence=0.99,
            )
        )

        llm = (
            MedicalDocumentExtraction(
                document_id=(
                    "document-123"
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
                                    "Incorrect Name"
                                ),
                                confidence=0.80,
                                extraction_method=(
                                    ExtractionMethod
                                    .LLM
                                ),
                                sources=[
                                    self.source
                                ],
                            )
                        )
                    )
                ),
                extraction_confidence=0.80,
            )
        )

        merged = (
            MedicalExtractionMergeService
            .merge(
                deterministic=(
                    deterministic
                ),
                llm=llm,
            )
        )

        self.assertEqual(
            merged.patient.name.value,
            "Synthetic Patient",
        )

    def test_different_document_ids_are_rejected(
        self,
    ) -> None:
        deterministic = (
            MedicalDocumentExtraction(
                document_id=(
                    "document-123"
                ),
                document_type=(
                    MedicalDocumentType
                    .UNKNOWN
                ),
                extraction_confidence=0.0,
            )
        )

        llm = (
            MedicalDocumentExtraction(
                document_id=(
                    "document-456"
                ),
                document_type=(
                    MedicalDocumentType
                    .UNKNOWN
                ),
                extraction_confidence=0.0,
            )
        )

        with self.assertRaises(
            ValueError
        ):
            (
                MedicalExtractionMergeService
                .merge(
                    deterministic=(
                        deterministic
                    ),
                    llm=llm,
                )
            )


if __name__ == "__main__":
    unittest.main()
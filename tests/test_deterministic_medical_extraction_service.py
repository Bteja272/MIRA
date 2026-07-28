import unittest

from app.schemas.medical_extraction import (
    ExtractionMethod,
    LabResultFlag,
    MedicationStatus,
)
from app.services.deterministic_medical_extraction_service import (
    DeterministicMedicalExtractionService,
)


class DeterministicMedicalExtractionTests(
    unittest.TestCase
):
    def setUp(self) -> None:
        self.document = {
            "document_id": (
                "document-123"
            ),
            "filename": (
                "synthetic_lab_report.txt"
            ),
            "document_type": (
                "lab_report"
            ),
        }

    def test_extracts_patient_dates_labs_and_medication(
        self,
    ) -> None:
        chunks = [
            {
                "chunk_id": "chunk-1",
                "document_id": (
                    "document-123"
                ),
                "page_number": 1,
                "chunk_index": 0,
                "text": (
                    "Patient Name: Synthetic Patient\n"
                    "Date of Birth: January 1, 1990\n"
                    "Report Date: 2026-07-20\n"
                    "Hemoglobin: 13.8 g/dL "
                    "(12.0-16.0) Normal\n"
                    "Glucose: 110 mg/dL "
                    "Reference Range: 70-99 High\n"
                    "Medication: Aspirin 81 mg "
                    "by mouth once daily"
                ),
            }
        ]

        extraction = (
            DeterministicMedicalExtractionService
            .extract(
                document=self.document,
                chunks=chunks,
            )
        )

        self.assertEqual(
            extraction.patient.name.value,
            "Synthetic Patient",
        )

        self.assertEqual(
            str(
                extraction.patient
                .date_of_birth
                .normalized_value
            ),
            "1990-01-01",
        )

        self.assertEqual(
            str(
                extraction.document_date
                .normalized_value
            ),
            "2026-07-20",
        )

        self.assertEqual(
            len(extraction.lab_results),
            2,
        )

        hemoglobin = (
            extraction.lab_results[0]
        )

        self.assertEqual(
            hemoglobin.test_name,
            "Hemoglobin",
        )

        self.assertEqual(
            hemoglobin.numeric_value,
            13.8,
        )

        self.assertEqual(
            hemoglobin.unit,
            "g/dL",
        )

        self.assertEqual(
            hemoglobin.flag,
            LabResultFlag.NORMAL,
        )

        glucose = (
            extraction.lab_results[1]
        )

        self.assertEqual(
            glucose.flag,
            LabResultFlag.HIGH,
        )

        self.assertEqual(
            len(extraction.medications),
            1,
        )

        medication = (
            extraction.medications[0]
        )

        self.assertEqual(
            medication.name,
            "Aspirin",
        )

        self.assertEqual(
            medication.dose,
            "81 mg",
        )

        self.assertEqual(
            medication.route,
            "oral",
        )

        self.assertEqual(
            medication.frequency,
            "once daily",
        )

        self.assertEqual(
            medication.status,
            MedicationStatus.CURRENT,
        )

        self.assertEqual(
            medication.extraction_method,
            (
                ExtractionMethod
                .DETERMINISTIC
            ),
        )

    def test_does_not_infer_flag_from_reference_range(
        self,
    ) -> None:
        chunks = [
            {
                "chunk_id": "chunk-1",
                "document_id": (
                    "document-123"
                ),
                "page_number": 1,
                "chunk_index": 0,
                "text": (
                    "Glucose: 110 mg/dL "
                    "Reference Range: 70-99"
                ),
            }
        ]

        extraction = (
            DeterministicMedicalExtractionService
            .extract(
                document=self.document,
                chunks=chunks,
            )
        )

        self.assertEqual(
            extraction.lab_results[
                0
            ].flag,
            LabResultFlag.UNKNOWN,
        )

    def test_ignores_non_lab_numeric_metadata(
        self,
    ) -> None:
        chunks = [
            {
                "chunk_id": "chunk-1",
                "document_id": (
                    "document-123"
                ),
                "page_number": 1,
                "chunk_index": 0,
                "text": (
                    "Patient ID: 12345\n"
                    "Age: 45\n"
                    "Room Number: 203"
                ),
            }
        ]

        extraction = (
            DeterministicMedicalExtractionService
            .extract(
                document=self.document,
                chunks=chunks,
            )
        )

        self.assertEqual(
            extraction.lab_results,
            [],
        )

    def test_source_metadata_comes_from_chunk(
        self,
    ) -> None:
        chunks = [
            {
                "chunk_id": "chunk-abc",
                "document_id": (
                    "document-123"
                ),
                "page_number": 3,
                "chunk_index": 7,
                "text": (
                    "Hemoglobin: 13.8 g/dL"
                ),
            }
        ]

        extraction = (
            DeterministicMedicalExtractionService
            .extract(
                document=self.document,
                chunks=chunks,
            )
        )

        source = (
            extraction.lab_results[
                0
            ].sources[0]
        )

        self.assertEqual(
            source.document_id,
            "document-123",
        )

        self.assertEqual(
            source.chunk_id,
            "chunk-abc",
        )

        self.assertEqual(
            source.page_number,
            3,
        )

        self.assertEqual(
            source.chunk_index,
            7,
        )


if __name__ == "__main__":
    unittest.main()
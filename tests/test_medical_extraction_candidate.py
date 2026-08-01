import unittest

from app.schemas.medical_extraction import (
    DiagnosisStatus,
    LabResultFlag,
    MedicationStatus,
)
from app.schemas.medical_extraction_candidate import (
    MedicalExtractionCandidate,
)


class MedicalExtractionCandidateTests(
    unittest.TestCase
):
    def test_null_placeholder_rows_are_removed(
        self,
    ) -> None:
        candidate = (
            MedicalExtractionCandidate
            .model_validate(
                {
                    "patient": None,
                    "providers": [
                        {
                            "name": None,
                            "role": None,
                        }
                    ],
                    "diagnoses": [
                        {
                            "name": None,
                            "status": None,
                        }
                    ],
                    "medications": [
                        {
                            "name": None,
                            "status": None,
                        }
                    ],
                    "lab_results": [
                        {
                            "test_name": None,
                            "raw_value": None,
                            "flag": None,
                        }
                    ],
                    "procedures": [
                        {
                            "name": None,
                        }
                    ],
                    "follow_up_instructions": [
                        {
                            "instruction": None,
                        }
                    ],
                }
            )
        )

        self.assertEqual(
            candidate.providers,
            [],
        )
        self.assertEqual(
            candidate.diagnoses,
            [],
        )
        self.assertEqual(
            candidate.medications,
            [],
        )
        self.assertEqual(
            candidate.lab_results,
            [],
        )
        self.assertEqual(
            candidate.procedures,
            [],
        )
        self.assertEqual(
            candidate.follow_up_instructions,
            [],
        )

    def test_valid_rows_survive_placeholder_cleanup(
        self,
    ) -> None:
        candidate = (
            MedicalExtractionCandidate
            .model_validate(
                {
                    "diagnoses": [
                        {
                            "name": "Hypertension",
                            "status": None,
                        }
                    ],
                    "medications": [
                        {
                            "name": "Metformin",
                            "dose": "500 mg",
                            "status": None,
                        }
                    ],
                    "lab_results": [
                        {
                            "test_name": "Glucose",
                            "raw_value": 110,
                            "flag": None,
                        }
                    ],
                }
            )
        )

        self.assertEqual(
            candidate.diagnoses[0].status,
            DiagnosisStatus.UNKNOWN,
        )
        self.assertEqual(
            candidate.medications[0].status,
            MedicationStatus.UNKNOWN,
        )
        self.assertEqual(
            candidate.lab_results[0].raw_value,
            "110",
        )
        self.assertEqual(
            candidate.lab_results[0].flag,
            LabResultFlag.UNKNOWN,
        )

    def test_null_top_level_lists_become_empty(
        self,
    ) -> None:
        candidate = (
            MedicalExtractionCandidate
            .model_validate(
                {
                    "providers": None,
                    "diagnoses": None,
                    "medications": None,
                    "lab_results": None,
                    "procedures": None,
                    "follow_up_instructions": None,
                }
            )
        )

        self.assertEqual(
            candidate.providers,
            [],
        )
        self.assertEqual(
            candidate.lab_results,
            [],
        )

    def test_placeholder_strings_are_removed(
        self,
    ) -> None:
        candidate = (
            MedicalExtractionCandidate
            .model_validate(
                {
                    "patient": {
                        "name": "unknown",
                    },
                    "providers": [
                        {
                            "name": "N/A",
                        }
                    ],
                    "diagnoses": [
                        {
                            "name": "null",
                        }
                    ],
                }
            )
        )

        self.assertIsNone(
            candidate.patient.name
        )
        self.assertEqual(
            candidate.providers,
            [],
        )
        self.assertEqual(
            candidate.diagnoses,
            [],
        )

    def test_candidate_lists_are_bounded(
        self,
    ) -> None:
        candidate = (
            MedicalExtractionCandidate
            .model_validate(
                {
                    "providers": [
                        {
                            "name": f"Provider {index}"
                        }
                        for index in range(75)
                    ]
                }
            )
        )

        self.assertEqual(
            len(candidate.providers),
            50,
        )


if __name__ == "__main__":
    unittest.main()
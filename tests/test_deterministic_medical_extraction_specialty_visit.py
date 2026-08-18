import unittest

from app.services.deterministic_medical_extraction_service import (
    DeterministicMedicalExtractionService,
)


class DeterministicMedicationSpecialtyVisitTests(
    unittest.TestCase
):
    def setUp(self) -> None:
        self.document = {
            "document_id": "eval-visit-2026-05-12",
            "filename": "synthetic_specialty_visit_2026-05-12.txt",
            "document_type": "visit_note",
        }

    @staticmethod
    def _chunk(
        chunk_id: str,
        chunk_index: int,
        text: str,
    ) -> dict:
        return {
            "chunk_id": chunk_id,
            "page_number": 1,
            "chunk_index": chunk_index,
            "text": text,
        }

    def test_specialty_visit_list_wording_preserves_frequencies(
        self,
    ) -> None:
        chunks = [
            self._chunk(
                "eval-visit-may-c1",
                0,
                (
                    "Specialty Visit dated 2026-05-12. "
                    "Medication section lists atorvastatin "
                    "40 mg nightly."
                ),
            ),
            self._chunk(
                "eval-visit-may-c2",
                1,
                (
                    "The same note lists metformin "
                    "500 mg twice daily."
                ),
            ),
        ]

        medications = (
            DeterministicMedicalExtractionService
            ._extract_medications(
                document=self.document,
                chunks=chunks,
            )
        )

        actual = {
            (
                item.name.casefold(),
                item.dose.casefold(),
            ): item.frequency
            for item in medications
        }

        self.assertEqual(
            actual[
                (
                    "atorvastatin",
                    "40 mg",
                )
            ],
            "nightly",
        )
        self.assertEqual(
            actual[
                (
                    "metformin",
                    "500 mg",
                )
            ],
            "twice daily",
        )


if __name__ == "__main__":
    unittest.main()
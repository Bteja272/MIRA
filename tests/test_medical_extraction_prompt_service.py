import unittest

from app.schemas.medical_extraction import (
    ExtractionMethod,
    ExtractionStatus,
    MedicalDocumentExtraction,
    MedicalDocumentType,
    PatientInformation,
    SourceEvidence,
    SourcedTextValue,
)
from app.services.medical_extraction_prompt_service import (
    MedicalExtractionPromptService,
)


class MedicalExtractionPromptServiceTests(
    unittest.TestCase
):
    def setUp(self) -> None:
        self.document = {
            "document_id": "document-123",
            "filename": "synthetic.txt",
            "document_type": "lab_report",
        }
        self.chunks = [
            {
                "chunk_id": "chunk-1",
                "page_number": 1,
                "chunk_index": 0,
                "text": (
                    "Patient: Synthetic Patient\n"
                    "Provider: Dr. Example"
                ),
            }
        ]

    def test_prompt_uses_lightweight_contract(
        self,
    ) -> None:
        prompt = (
            MedicalExtractionPromptService
            .build_extraction_prompt(
                document=self.document,
                chunks=self.chunks,
            )
        )

        self.assertIn(
            '"patient"',
            prompt,
        )
        self.assertIn(
            '"providers"',
            prompt,
        )
        self.assertIn(
            "Return no confidence values",
            prompt,
        )
        self.assertNotIn("$defs", prompt)
        self.assertNotIn(
            '"schema_version"',
            prompt,
        )
        self.assertNotIn(
            '"extraction_method"',
            prompt,
        )

    def test_prompt_lists_deterministic_facts(
        self,
    ) -> None:
        deterministic = MedicalDocumentExtraction(
            document_id="document-123",
            document_type=(
                MedicalDocumentType.LAB_REPORT
            ),
            status=ExtractionStatus.PARTIAL,
            patient=PatientInformation(
                name=SourcedTextValue(
                    value="Synthetic Patient",
                    confidence=0.99,
                    extraction_method=(
                        ExtractionMethod
                        .DETERMINISTIC
                    ),
                    sources=[
                        SourceEvidence(
                            document_id=(
                                "document-123"
                            ),
                            chunk_id="chunk-1",
                            source_filename=(
                                "synthetic.txt"
                            ),
                            page_number=1,
                            chunk_index=0,
                            quoted_text=(
                                "Patient: "
                                "Synthetic Patient"
                            ),
                        )
                    ],
                )
            ),
            extraction_confidence=0.99,
        )

        prompt = (
            MedicalExtractionPromptService
            .build_extraction_prompt(
                document=self.document,
                chunks=self.chunks,
                deterministic_extraction=(
                    deterministic
                ),
            )
        )

        self.assertIn(
            "patient.name=Synthetic Patient",
            prompt,
        )
        self.assertIn(
            "do not repeat",
            prompt.casefold(),
        )


    def test_prompt_requires_lowercase_enum_control_values(
        self,
    ) -> None:
        prompt = (
            MedicalExtractionPromptService
            .build_extraction_prompt(
                document=self.document,
                chunks=self.chunks,
            )
        )

        normalized_prompt = " ".join(
            prompt.split()
        )

        self.assertIn(
            "exact lowercase tokens",
            normalized_prompt,
        )
        self.assertIn(
            '"High" must be returned as "high"',
            normalized_prompt,
        )
        self.assertIn(
            '"Normal" must be returned as "normal"',
            normalized_prompt,
        )

    def test_repair_prompt_is_bounded(
        self,
    ) -> None:
        repair_prompt = (
            MedicalExtractionPromptService
            .build_repair_prompt(
                original_prompt="x" * 20_000,
                invalid_output="y" * 20_000,
                validation_error="z" * 10_000,
            )
        )

        # Small formatting overhead above the configured budget is
        # acceptable, but the request must remain bounded.
        self.assertLess(
            len(repair_prompt),
            14_000,
        )


if __name__ == "__main__":
    unittest.main()
import unittest

from app.services.response_validation_service import (
    ResponseValidationService,
)


class GroundedResponseValidationTests(
    unittest.TestCase
):
    def test_missing_citation_is_detected(
        self,
    ) -> None:
        result = (
            ResponseValidationService
            .validate_grounded_answer(
                answer=(
                    "The documented HbA1c "
                    "is 7.2 %."
                ),
                sources=[
                    {
                        "source_number": 1,
                        "document_id": "doc-1",
                        "text": (
                            "Hemoglobin A1c: "
                            "7.2 %."
                        ),
                    }
                ],
            )
        )

        self.assertFalse(
            result.is_valid
        )
        self.assertIn(
            "missing_source_citation",
            result.issues,
        )

    def test_derived_value_is_rejected(
        self,
    ) -> None:
        result = (
            ResponseValidationService
            .validate_grounded_answer(
                answer=(
                    "HbA1c changed from "
                    "7.2 % [Source 1] to "
                    "6.8 % [Source 2], a "
                    "0.4 % difference."
                ),
                sources=[
                    {
                        "source_number": 1,
                        "text": (
                            "Hemoglobin A1c: "
                            "7.2 %."
                        ),
                    },
                    {
                        "source_number": 2,
                        "text": (
                            "Hemoglobin A1c: "
                            "6.8 %."
                        ),
                    },
                ],
            )
        )

        self.assertFalse(
            result.is_valid
        )
        self.assertIn(
            "0.4 %",
            result
            .unsupported_medical_values,
        )

    def test_wrong_source_for_dose_is_detected(
        self,
    ) -> None:
        result = (
            ResponseValidationService
            .validate_grounded_answer(
                answer=(
                    "Atorvastatin 20 mg "
                    "[Source 2]."
                ),
                sources=[
                    {
                        "source_number": 1,
                        "text": (
                            "Atorvastatin 20 mg "
                            "nightly."
                        ),
                    },
                    {
                        "source_number": 2,
                        "text": (
                            "Atorvastatin 40 mg "
                            "nightly."
                        ),
                    },
                ],
            )
        )

        self.assertFalse(
            result.is_valid
        )
        self.assertIn(
            "20 mg",
            result
            .misattributed_medical_values,
        )

    def test_supported_cited_value_passes(
        self,
    ) -> None:
        result = (
            ResponseValidationService
            .validate_grounded_answer(
                answer=(
                    "Atorvastatin 20 mg "
                    "[Source 1]."
                ),
                sources=[
                    {
                        "source_number": 1,
                        "text": (
                            "Atorvastatin 20 mg "
                            "nightly."
                        ),
                    }
                ],
            )
        )

        self.assertTrue(
            result.is_valid
        )


if __name__ == "__main__":
    unittest.main()
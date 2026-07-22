import unittest

from app.services.response_validation_service import (
    ResponseValidationService,
)


class ResponseValidationServiceTests(
    unittest.TestCase
):
    def test_removes_unsupported_range_interpretation(
        self,
    ):
        answer = """
### Laboratory Results

- Total Cholesterol: 196 mg/dL [Source 1]
Reference Range: Below 200 mg/dL
Documented flag: Normal
Result is above reference range.

- HDL Cholesterol: 48 mg/dL [Source 1]
Reference Range: 40 - 60 mg/dL
Documented flag: Normal
Result is within reference range.
""".strip()

        sanitized = (
            ResponseValidationService
            .sanitize_document_answer(
                answer
            )
        )

        self.assertNotIn(
            "above reference range",
            sanitized.lower(),
        )

        self.assertNotIn(
            "within reference range",
            sanitized.lower(),
        )

        self.assertIn(
            (
                "Reference Range: "
                "Below 200 mg/dL"
            ),
            sanitized,
        )

        self.assertIn(
            "Documented flag: Normal",
            sanitized,
        )

    def test_detects_markdown_formatted_interpretation(
        self,
    ):
        value = (
            "Result is **outside of "
            "reference range**."
        )

        self.assertTrue(
            ResponseValidationService
            .contains_unsupported_interpretation(
                value
            )
        )


if __name__ == "__main__":
    unittest.main()
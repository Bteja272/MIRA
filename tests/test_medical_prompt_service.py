import unittest

from app.services.medical_prompt_service import (
    MedicalPromptService,
)


class MedicalPromptServiceTests(unittest.TestCase):
    def test_document_prompt_contains_required_boundaries(
        self,
    ):
        prompt = (
            MedicalPromptService
            .document_system_prompt()
            .lower()
        )

        self.assertIn(
            "use only information present",
            prompt,
        )
        self.assertIn(
            "do not diagnose",
            prompt,
        )
        self.assertIn(
            "do not prescribe medication",
            prompt,
        )
        self.assertIn(
            "do not provide a prognosis",
            prompt,
        )
        self.assertIn(
            "do not invent",
            prompt,
        )
        self.assertIn(
            "[source 1]",
            prompt,
        )

    def test_document_prompt_contains_lab_safety_rules(
        self,
    ):
        prompt = (
            MedicalPromptService
            .document_system_prompt()
            .lower()
        )

        self.assertIn(
            "reference range",
            prompt,
        )
        self.assertIn(
            "documented flag",
            prompt,
        )
        self.assertIn(
            "do not independently classify",
            prompt,
        )
        self.assertIn(
            "do not combine neighboring laboratory tests",
            prompt,
        )
        self.assertIn(
            "copy numerical values",
            prompt,
        )

    def test_document_prompt_does_not_request_disclaimer(
        self,
    ):
        prompt = (
            MedicalPromptService
            .document_system_prompt()
            .lower()
        )

        self.assertIn(
            "application adds",
            prompt,
        )
        self.assertIn(
            "disclaimer",
            prompt,
        )

    def test_general_prompt_contains_required_boundaries(
        self,
    ):
        prompt = (
            MedicalPromptService
            .general_system_prompt()
            .lower()
        )

        self.assertIn(
            "do not diagnose",
            prompt,
        )
        self.assertIn(
            "do not prescribe medication",
            prompt,
        )
        self.assertIn(
            "do not tell the user to start, stop",
            prompt,
        )
        self.assertIn(
            "do not provide a definite prognosis",
            prompt,
        )
        self.assertIn(
            "licensed healthcare professional",
            prompt,
        )

    def test_general_prompt_does_not_claim_document_access(
        self,
    ):
        prompt = (
            MedicalPromptService
            .general_system_prompt()
            .lower()
        )

        self.assertIn(
            "do not claim access to medical documents",
            prompt,
        )

    def test_web_prompt_requires_web_context(
        self,
    ):
        prompt = (
            MedicalPromptService
            .web_system_prompt()
            .lower()
        )

        self.assertIn(
            "supplied web-search context",
            prompt,
        )
        self.assertIn(
            "cite claims",
            prompt,
        )
        self.assertIn(
            "web-source labels",
            prompt,
        )
        self.assertIn(
            "do not invent medical claims",
            prompt,
        )

    def test_web_prompt_contains_medical_boundaries(
        self,
    ):
        prompt = (
            MedicalPromptService
            .web_system_prompt()
            .lower()
        )

        self.assertIn(
            "do not diagnose",
            prompt,
        )
        self.assertIn(
            "do not prescribe medication",
            prompt,
        )
        self.assertIn(
            "do not provide a definite prognosis",
            prompt,
        )

    def test_ensure_disclaimer_adds_disclaimer(
        self,
    ):
        answer = "The document lists a glucose result."

        result = (
            MedicalPromptService
            .ensure_disclaimer(answer)
        )

        self.assertIn(
            answer,
            result,
        )
        self.assertIn(
            MedicalPromptService.DISCLAIMER,
            result,
        )

    def test_ensure_disclaimer_does_not_duplicate_it(
        self,
    ):
        answer = (
            "Educational explanation.\n\n"
            f"{MedicalPromptService.DISCLAIMER}"
        )

        result = (
            MedicalPromptService
            .ensure_disclaimer(answer)
        )

        self.assertEqual(
            result.count(
                MedicalPromptService.DISCLAIMER
            ),
            1,
        )

    def test_ensure_disclaimer_handles_empty_answer(
        self,
    ):
        result = (
            MedicalPromptService
            .ensure_disclaimer("")
        )

        self.assertEqual(
            result,
            MedicalPromptService.DISCLAIMER,
        )


if __name__ == "__main__":
    unittest.main()
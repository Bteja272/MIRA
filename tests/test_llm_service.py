import unittest
from unittest.mock import (
    Mock,
    patch,
)

from app.services.llm_service import (
    LLMService,
)


class LLMServiceTests(unittest.TestCase):

    @patch(
        "app.services.llm_service."
        "LLMProviderFactory.create"
    )
    @patch(
        "app.services.llm_service.settings"
    )
    def test_custom_system_prompt_is_sent(
        self,
        mock_settings,
        mock_create,
    ) -> None:
        mock_settings.llm_provider = "groq"
        mock_settings.llm_fallback_provider = ""

        provider = Mock()
        provider.generate.return_value = (
            "Synthetic response"
        )

        mock_create.return_value = provider

        result = LLMService.generate_response(
            prompt="Synthetic question",
            system_prompt=(
                "Synthetic system prompt"
            ),
            temperature=0.0,
        )

        self.assertEqual(
            result,
            "Synthetic response",
        )

        provider.generate.assert_called_once()

        request = (
            provider.generate
            .call_args
            .args[0]
        )

        self.assertEqual(
            request.prompt,
            "Synthetic question",
        )

        self.assertEqual(
            request.system_prompt,
            "Synthetic system prompt",
        )

        self.assertEqual(
            request.temperature,
            0.0,
        )

    @patch(
        "app.services.llm_service."
        "LLMProviderFactory.create"
    )
    @patch(
        "app.services.llm_service.settings"
    )
    def test_primary_provider_is_used(
        self,
        mock_settings,
        mock_create,
    ) -> None:
        mock_settings.llm_provider = "groq"
        mock_settings.llm_fallback_provider = (
            "ollama"
        )

        provider = Mock()
        provider.generate.return_value = (
            "Primary response"
        )

        mock_create.return_value = provider

        result = LLMService.generate_response(
            prompt="Synthetic question"
        )

        self.assertEqual(
            result,
            "Primary response",
        )

        mock_create.assert_called_once_with(
            "groq"
        )

    @patch(
        "app.services.llm_service."
        "LLMProviderFactory.create"
    )
    @patch(
        "app.services.llm_service.settings"
    )
    def test_fallback_provider_is_used(
        self,
        mock_settings,
        mock_create,
    ) -> None:
        mock_settings.llm_provider = "groq"
        mock_settings.llm_fallback_provider = (
            "ollama"
        )

        primary_provider = Mock()
        primary_provider.generate.side_effect = (
            RuntimeError(
                "Groq unavailable"
            )
        )

        fallback_provider = Mock()
        fallback_provider.generate.return_value = (
            "Fallback response"
        )

        mock_create.side_effect = [
            primary_provider,
            fallback_provider,
        ]

        result = LLMService.generate_response(
            prompt="Synthetic question"
        )

        self.assertEqual(
            result,
            "Fallback response",
        )

        self.assertEqual(
            mock_create.call_count,
            2,
        )

        self.assertEqual(
            mock_create.call_args_list[0].args,
            ("groq",),
        )

        self.assertEqual(
            mock_create.call_args_list[1].args,
            ("ollama",),
        )

    @patch(
        "app.services.llm_service."
        "LLMProviderFactory.create"
    )
    @patch(
        "app.services.llm_service.settings"
    )
    def test_provider_failure_without_fallback_raises(
        self,
        mock_settings,
        mock_create,
    ) -> None:
        mock_settings.llm_provider = "groq"
        mock_settings.llm_fallback_provider = ""

        provider = Mock()
        provider.generate.side_effect = (
            RuntimeError(
                "Provider unavailable"
            )
        )

        mock_create.return_value = provider

        with self.assertRaisesRegex(
            RuntimeError,
            "LLM generation failed using groq",
        ):
            LLMService.generate_response(
                prompt="Synthetic question"
            )

    def test_blank_prompt_is_rejected(
        self,
    ) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "prompt is required",
        ):
            LLMService.generate_response(
                prompt="   "
            )


if __name__ == "__main__":
    unittest.main()
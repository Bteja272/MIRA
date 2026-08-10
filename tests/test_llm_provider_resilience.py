import unittest
from unittest.mock import (
    Mock,
    call,
    patch,
)

from app.services.llm_providers.base import (
    LLMProviderError,
)
from app.services.llm_providers.retry_policy import (
    LLMRetryPolicy,
)
from app.services.llm_service import (
    LLMService,
)


class LLMProviderResilienceTests(
    unittest.TestCase
):
    def setUp(self) -> None:
        self.retry_policy = (
            LLMRetryPolicy(
                max_retries=1,
                base_delay_seconds=0.0,
                max_delay_seconds=0.0,
                retry_after_cap_seconds=0.0,
            )
        )

    @patch(
        "app.services.llm_service."
        "LLMRetryPolicy.from_environment"
    )
    @patch(
        "app.services.llm_service."
        "LLMProviderFactory.create"
    )
    @patch(
        "app.services.llm_service.settings"
    )
    def test_retryable_primary_failure_retries_same_provider(
        self,
        mock_settings,
        mock_create,
        mock_policy,
    ) -> None:
        mock_settings.llm_provider = (
            "groq"
        )
        mock_settings.llm_fallback_provider = (
            "ollama"
        )
        mock_policy.return_value = (
            self.retry_policy
        )

        provider = Mock()
        provider.model_name = (
            "openai/gpt-oss-20b"
        )
        provider.generate.side_effect = [
            LLMProviderError(
                "groq",
                "rate limited",
                retryable=True,
                kind="rate_limit",
                status_code=429,
                fallback_allowed=True,
            ),
            "Recovered",
        ]
        mock_create.return_value = provider

        result = (
            LLMService
            .generate_response_with_metadata(
                prompt="Synthetic prompt"
            )
        )

        self.assertEqual(
            result.text,
            "Recovered",
        )
        self.assertFalse(
            result.metadata.fallback_used
        )
        self.assertEqual(
            result.metadata.attempts,
            2,
        )
        mock_create.assert_called_once_with(
            "groq"
        )
        self.assertEqual(
            provider.generate.call_count,
            2,
        )

    @patch(
        "app.services.llm_service."
        "LLMRetryPolicy.from_environment"
    )
    @patch(
        "app.services.llm_service."
        "LLMProviderFactory.create"
    )
    @patch(
        "app.services.llm_service.settings"
    )
    def test_retry_exhaustion_uses_fallback(
        self,
        mock_settings,
        mock_create,
        mock_policy,
    ) -> None:
        mock_settings.llm_provider = (
            "groq"
        )
        mock_settings.llm_fallback_provider = (
            "ollama"
        )
        mock_policy.return_value = (
            self.retry_policy
        )

        primary = Mock()
        primary.model_name = (
            "openai/gpt-oss-20b"
        )
        primary.generate.side_effect = (
            LLMProviderError(
                "groq",
                "service unavailable",
                retryable=True,
                kind="server",
                status_code=503,
                fallback_allowed=True,
            )
        )

        fallback = Mock()
        fallback.model_name = (
            "llama3.2:latest"
        )
        fallback.generate.return_value = (
            "Fallback response"
        )

        mock_create.side_effect = [
            primary,
            fallback,
        ]

        result = (
            LLMService
            .generate_response_with_metadata(
                prompt="Synthetic prompt"
            )
        )

        self.assertEqual(
            result.text,
            "Fallback response",
        )
        self.assertTrue(
            result.metadata.fallback_used
        )
        self.assertEqual(
            result.metadata.provider,
            "ollama",
        )
        self.assertEqual(
            result.metadata.attempts,
            3,
        )
        self.assertEqual(
            mock_create.call_args_list,
            [
                call("groq"),
                call("ollama"),
            ],
        )

    @patch(
        "app.services.llm_service."
        "LLMRetryPolicy.from_environment"
    )
    @patch(
        "app.services.llm_service."
        "LLMProviderFactory.create"
    )
    @patch(
        "app.services.llm_service.settings"
    )
    def test_structured_output_failure_retries_but_does_not_fallback(
        self,
        mock_settings,
        mock_create,
        mock_policy,
    ) -> None:
        mock_settings.llm_provider = (
            "groq"
        )
        mock_settings.llm_fallback_provider = (
            "ollama"
        )
        mock_policy.return_value = (
            self.retry_policy
        )

        primary = Mock()
        primary.model_name = (
            "openai/gpt-oss-20b"
        )
        primary.generate.side_effect = (
            LLMProviderError(
                "groq",
                "structured output failed",
                retryable=True,
                kind="structured_output",
                status_code=400,
                error_code=(
                    "json_validate_failed"
                ),
                fallback_allowed=False,
            )
        )

        mock_create.return_value = (
            primary
        )

        with self.assertRaisesRegex(
            RuntimeError,
            "LLM generation failed using groq",
        ):
            LLMService.generate_response(
                prompt="Synthetic prompt"
            )

        self.assertEqual(
            primary.generate.call_count,
            2,
        )
        mock_create.assert_called_once_with(
            "groq"
        )

    @patch(
        "app.services.llm_service."
        "LLMRetryPolicy.from_environment"
    )
    @patch(
        "app.services.llm_service."
        "LLMProviderFactory.create"
    )
    @patch(
        "app.services.llm_service.settings"
    )
    def test_authentication_failure_does_not_retry_or_fallback(
        self,
        mock_settings,
        mock_create,
        mock_policy,
    ) -> None:
        mock_settings.llm_provider = (
            "groq"
        )
        mock_settings.llm_fallback_provider = (
            "ollama"
        )
        mock_policy.return_value = (
            self.retry_policy
        )

        primary = Mock()
        primary.model_name = (
            "openai/gpt-oss-20b"
        )
        primary.generate.side_effect = (
            LLMProviderError(
                "groq",
                "invalid credentials",
                retryable=False,
                kind="authentication",
                status_code=401,
                fallback_allowed=False,
            )
        )

        mock_create.return_value = (
            primary
        )

        with self.assertRaisesRegex(
            RuntimeError,
            "LLM generation failed using groq",
        ):
            LLMService.generate_response(
                prompt="Synthetic prompt"
            )

        primary.generate.assert_called_once()
        mock_create.assert_called_once_with(
            "groq"
        )

    @patch(
        "app.services.llm_service."
        "LLMRetryPolicy.from_environment"
    )
    @patch(
        "app.services.llm_service."
        "LLMProviderFactory.create"
    )
    @patch(
        "app.services.llm_service.settings"
    )
    def test_generic_primary_failure_preserves_backward_compatible_fallback(
        self,
        mock_settings,
        mock_create,
        mock_policy,
    ) -> None:
        mock_settings.llm_provider = (
            "groq"
        )
        mock_settings.llm_fallback_provider = (
            "ollama"
        )
        mock_policy.return_value = (
            self.retry_policy
        )

        primary = Mock()
        primary.model_name = "groq-model"
        primary.generate.side_effect = (
            RuntimeError(
                "unexpected"
            )
        )

        fallback = Mock()
        fallback.model_name = (
            "ollama-model"
        )
        fallback.generate.return_value = (
            "Fallback response"
        )

        mock_create.side_effect = [
            primary,
            fallback,
        ]

        result = (
            LLMService.generate_response(
                prompt="Synthetic prompt"
            )
        )

        self.assertEqual(
            result,
            "Fallback response",
        )

    @patch(
        "app.services.llm_service."
        "LLMRetryPolicy.from_environment"
    )
    @patch(
        "app.services.llm_service."
        "LLMProviderFactory.create"
    )
    @patch(
        "app.services.llm_service.settings"
    )
    def test_both_providers_fail_with_sanitized_error(
        self,
        mock_settings,
        mock_create,
        mock_policy,
    ) -> None:
        mock_settings.llm_provider = (
            "groq"
        )
        mock_settings.llm_fallback_provider = (
            "ollama"
        )
        mock_policy.return_value = (
            LLMRetryPolicy(
                max_retries=0,
                base_delay_seconds=0,
                max_delay_seconds=0,
                retry_after_cap_seconds=0,
            )
        )

        primary = Mock()
        primary.model_name = "groq-model"
        primary.generate.side_effect = (
            LLMProviderError(
                "groq",
                "temporary outage",
                retryable=True,
                kind="server",
                fallback_allowed=True,
            )
        )

        fallback = Mock()
        fallback.model_name = (
            "ollama-model"
        )
        fallback.generate.side_effect = (
            LLMProviderError(
                "ollama",
                "temporary outage",
                retryable=True,
                kind="server",
                fallback_allowed=True,
            )
        )

        mock_create.side_effect = [
            primary,
            fallback,
        ]

        with self.assertRaisesRegex(
            RuntimeError,
            (
                "LLM generation failed using "
                "primary groq and fallback ollama"
            ),
        ) as context:
            LLMService.generate_response(
                prompt="Synthetic prompt"
            )

        self.assertNotIn(
            "Synthetic prompt",
            str(context.exception),
        )


if __name__ == "__main__":
    unittest.main()
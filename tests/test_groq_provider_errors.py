import unittest
from unittest.mock import (
    Mock,
    patch,
)

from app.services.llm_providers.base import (
    LLMProviderError,
    LLMRequest,
)
from app.services.llm_providers.groq_provider import (
    GroqProvider,
)


class GroqProviderErrorTests(
    unittest.TestCase
):
    def setUp(self) -> None:
        self.request = LLMRequest(
            prompt="Synthetic prompt",
            system_prompt="Synthetic system prompt",
            timeout_seconds=30,
        )

    @staticmethod
    def _configure_settings(
        mock_settings,
    ) -> None:
        secret = Mock()
        secret.get_secret_value.return_value = (
            "test-key"
        )

        mock_settings.groq_api_key = secret
        mock_settings.groq_base_url = (
            "https://api.groq.com/openai/v1"
        )
        mock_settings.groq_model_name = (
            "openai/gpt-oss-20b"
        )

    @patch(
        "app.services.llm_providers."
        "groq_provider.settings"
    )
    @patch(
        "app.services.llm_providers."
        "groq_provider.requests.post"
    )
    def test_rate_limit_is_retryable_and_respects_retry_after(
        self,
        mock_post,
        mock_settings,
    ) -> None:
        self._configure_settings(
            mock_settings
        )

        response = Mock()
        response.ok = False
        response.status_code = 429
        response.headers = {
            "retry-after": "1.5",
        }
        response.json.return_value = {
            "error": {
                "message": (
                    "Rate limit exceeded"
                ),
                "type": (
                    "rate_limit_error"
                ),
            }
        }
        mock_post.return_value = response

        provider = GroqProvider()

        with self.assertRaises(
            LLMProviderError
        ) as context:
            provider.generate(
                self.request
            )

        error = context.exception

        self.assertEqual(
            error.kind,
            "rate_limit",
        )
        self.assertTrue(
            error.retryable
        )
        self.assertTrue(
            error.fallback_allowed
        )
        self.assertEqual(
            error.retry_after_seconds,
            1.5,
        )

    @patch(
        "app.services.llm_providers."
        "groq_provider.settings"
    )
    @patch(
        "app.services.llm_providers."
        "groq_provider.requests.post"
    )
    def test_server_error_is_retryable_and_can_fallback(
        self,
        mock_post,
        mock_settings,
    ) -> None:
        self._configure_settings(
            mock_settings
        )

        response = Mock()
        response.ok = False
        response.status_code = 503
        response.headers = {}
        response.json.return_value = {
            "error": {
                "message": (
                    "Service unavailable"
                ),
            }
        }
        mock_post.return_value = response

        with self.assertRaises(
            LLMProviderError
        ) as context:
            GroqProvider().generate(
                self.request
            )

        error = context.exception

        self.assertEqual(
            error.kind,
            "server",
        )
        self.assertTrue(
            error.retryable
        )
        self.assertTrue(
            error.fallback_allowed
        )

    @patch(
        "app.services.llm_providers."
        "groq_provider.settings"
    )
    @patch(
        "app.services.llm_providers."
        "groq_provider.requests.post"
    )
    def test_structured_output_failure_does_not_leak_failed_generation(
        self,
        mock_post,
        mock_settings,
    ) -> None:
        self._configure_settings(
            mock_settings
        )

        response = Mock()
        response.ok = False
        response.status_code = 400
        response.headers = {}
        response.json.return_value = {
            "error": {
                "message": (
                    "Generated JSON does not "
                    "match the expected schema."
                ),
                "type": (
                    "invalid_request_error"
                ),
                "code": (
                    "json_validate_failed"
                ),
                "failed_generation": (
                    "SENSITIVE_SYNTHETIC_PATIENT_DATA"
                ),
            }
        }
        mock_post.return_value = response

        with self.assertRaises(
            LLMProviderError
        ) as context:
            GroqProvider().generate(
                self.request
            )

        error = context.exception

        self.assertEqual(
            error.kind,
            "structured_output",
        )
        self.assertTrue(
            error.retryable
        )
        self.assertFalse(
            error.fallback_allowed
        )
        self.assertEqual(
            error.error_code,
            "json_validate_failed",
        )
        self.assertNotIn(
            "SENSITIVE_SYNTHETIC_PATIENT_DATA",
            str(error),
        )

    @patch(
        "app.services.llm_providers."
        "groq_provider.settings"
    )
    @patch(
        "app.services.llm_providers."
        "groq_provider.requests.post"
    )
    def test_authentication_error_is_not_retryable_or_fallbackable(
        self,
        mock_post,
        mock_settings,
    ) -> None:
        self._configure_settings(
            mock_settings
        )

        response = Mock()
        response.ok = False
        response.status_code = 401
        response.headers = {}
        response.json.return_value = {
            "error": {
                "message": (
                    "Invalid API key"
                ),
            }
        }
        mock_post.return_value = response

        with self.assertRaises(
            LLMProviderError
        ) as context:
            GroqProvider().generate(
                self.request
            )

        error = context.exception

        self.assertEqual(
            error.kind,
            "authentication",
        )
        self.assertFalse(
            error.retryable
        )
        self.assertFalse(
            error.fallback_allowed
        )


if __name__ == "__main__":
    unittest.main()
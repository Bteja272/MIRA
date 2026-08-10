import unittest
from unittest.mock import (
    Mock,
    patch,
)

from app.services.llm_providers.base import (
    LLMProviderError,
    LLMRequest,
)
from app.services.llm_providers.ollama_provider import (
    OllamaProvider,
)


class OllamaProviderTests(unittest.TestCase):

    @staticmethod
    def _request() -> LLMRequest:
        return LLMRequest(
            prompt="Synthetic question",
            system_prompt=(
                "Synthetic system prompt"
            ),
            timeout_seconds=30,
            temperature=0.0,
        )

    @patch(
        "app.services.llm_providers."
        "ollama_provider.settings"
    )
    @patch(
        "app.services.llm_providers."
        "ollama_provider.requests.post"
    )
    def test_system_prompt_is_sent(
        self,
        mock_post,
        mock_settings,
    ) -> None:
        mock_settings.ollama_base_url = (
            "http://localhost:11434"
        )
        mock_settings.resolved_ollama_model_name = (
            "llama3.2"
        )

        response = Mock()
        response.ok = True
        response.json.return_value = {
            "message": {
                "content": (
                    "Synthetic response"
                )
            }
        }

        mock_post.return_value = response

        provider = OllamaProvider()

        result = provider.generate(
            self._request()
        )

        self.assertEqual(
            result,
            "Synthetic response",
        )

        _, kwargs = mock_post.call_args

        payload = kwargs["json"]

        self.assertEqual(
            payload["messages"][0],
            {
                "role": "system",
                "content": (
                    "Synthetic system prompt"
                ),
            },
        )

        self.assertEqual(
            payload["messages"][1],
            {
                "role": "user",
                "content": (
                    "Synthetic question"
                ),
            },
        )

    @patch(
        "app.services.llm_providers."
        "ollama_provider.settings"
    )
    @patch(
        "app.services.llm_providers."
        "ollama_provider.requests.post"
    )
    def test_ollama_error_includes_response_body(
        self,
        mock_post,
        mock_settings,
    ) -> None:
        mock_settings.ollama_base_url = (
            "http://localhost:11434"
        )
        mock_settings.resolved_ollama_model_name = (
            "llama3.2"
        )

        response = Mock()
        response.ok = False
        response.status_code = 500
        response.text = (
            "Synthetic Ollama failure"
        )

        mock_post.return_value = response

        provider = OllamaProvider()

        with self.assertRaises(
            LLMProviderError
        ) as context:
            provider.generate(
                self._request()
            )

        message = str(
            context.exception
        )

        self.assertIn(
            "HTTP 500",
            message,
        )

        self.assertIn(
            "Synthetic Ollama failure",
            message,
        )


if __name__ == "__main__":
    unittest.main()
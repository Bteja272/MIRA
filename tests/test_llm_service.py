import unittest
from unittest.mock import Mock, patch

from app.services.llm_service import LLMService


class LLMServiceTests(unittest.TestCase):
    @patch("app.services.llm_service.requests.post")
    def test_custom_system_prompt_is_sent(
        self,
        mock_post,
    ):
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "message": {
                "content": "Test response"
            }
        }
        mock_post.return_value = mock_response

        answer = LLMService.generate_response(
            prompt="Explain this.",
            system_prompt="Custom medical instructions.",
        )

        self.assertEqual(answer, "Test response")

        payload = mock_post.call_args.kwargs["json"]

        self.assertEqual(
            payload["messages"][0]["role"],
            "system",
        )
        self.assertEqual(
            payload["messages"][0]["content"],
            "Custom medical instructions.",
        )
        self.assertEqual(
            payload["messages"][1]["content"],
            "Explain this.",
        )

    @patch("app.services.llm_service.requests.post")
    def test_ollama_error_includes_response_body(
        self,
        mock_post,
    ):
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 404
        mock_response.text = "model not found"
        mock_post.return_value = mock_response

        with self.assertRaisesRegex(
            RuntimeError,
            "model not found",
        ):
            LLMService.generate_response("Hello")


if __name__ == "__main__":
    unittest.main()
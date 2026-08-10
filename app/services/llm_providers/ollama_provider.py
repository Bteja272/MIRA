from typing import Any

import requests

from app.core.config import settings
from app.services.llm_providers.base import (
    LLMProvider,
    LLMProviderError,
    LLMRequest,
)


class OllamaProvider(LLMProvider):
    name = "ollama"

    @property
    def model_name(self) -> str:
        return (
            settings
            .resolved_ollama_model_name
        )

    @staticmethod
    def _safe_error_message(
        response: requests.Response,
    ) -> str:
        message = "request failed"

        try:
            payload = response.json()
        except ValueError:
            payload = None

        if isinstance(payload, dict):
            raw_error = payload.get(
                "error"
            )

            if isinstance(
                raw_error,
                str,
            ) and raw_error.strip():
                message = raw_error.strip()

        if message == "request failed":
            raw_text = getattr(
                response,
                "text",
                "",
            )

            if isinstance(
                raw_text,
                str,
            ) and raw_text.strip():
                message = raw_text.strip()

        return message[:1000]

    @classmethod
    def _http_error(
        cls,
        response: requests.Response,
    ) -> LLMProviderError:
        status_code = int(
            response.status_code
        )
        provider_message = (
            cls._safe_error_message(
                response
            )
        )

        common_message = (
            f"request failed with HTTP "
            f"{status_code}: "
            f"{provider_message}"
        )

        if status_code in {
            408,
            429,
        }:
            return LLMProviderError(
                "ollama",
                common_message,
                retryable=True,
                kind=(
                    "rate_limit"
                    if status_code == 429
                    else "timeout"
                ),
                status_code=status_code,
                fallback_allowed=True,
            )

        if status_code >= 500:
            return LLMProviderError(
                "ollama",
                common_message,
                retryable=True,
                kind="server",
                status_code=status_code,
                fallback_allowed=True,
            )

        if status_code in {
            401,
            403,
        }:
            return LLMProviderError(
                "ollama",
                common_message,
                retryable=False,
                kind="authentication",
                status_code=status_code,
                fallback_allowed=False,
            )

        if status_code == 404:
            return LLMProviderError(
                "ollama",
                common_message,
                retryable=False,
                kind="configuration",
                status_code=status_code,
                fallback_allowed=False,
            )

        return LLMProviderError(
            "ollama",
            common_message,
            retryable=False,
            kind="request",
            status_code=status_code,
            fallback_allowed=False,
        )

    def generate(
        self,
        request: LLMRequest,
    ) -> str:
        url = (
            f"{settings.ollama_base_url.rstrip('/')}"
            "/api/chat"
        )

        options: dict[str, Any] = {}

        if request.temperature is not None:
            options["temperature"] = (
                request.temperature
            )

        if (
            request.max_output_tokens
            is not None
        ):
            options["num_predict"] = (
                request.max_output_tokens
            )

        if (
            request.context_window
            is not None
        ):
            options["num_ctx"] = (
                request.context_window
            )

        payload: dict[str, Any] = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        request.system_prompt
                    ),
                },
                {
                    "role": "user",
                    "content": request.prompt,
                },
            ],
            "stream": False,
        }

        if request.json_schema is not None:
            payload["format"] = (
                request.json_schema
            )

        elif request.json_mode:
            payload["format"] = "json"

        if options:
            payload["options"] = options

        if request.keep_alive:
            payload["keep_alive"] = (
                request.keep_alive
            )

        try:
            response = requests.post(
                url,
                json=payload,
                timeout=request.timeout_seconds,
            )

        except requests.Timeout as exc:
            raise LLMProviderError(
                "ollama",
                "request timed out.",
                retryable=True,
                kind="timeout",
                fallback_allowed=True,
            ) from exc

        except requests.RequestException as exc:
            raise LLMProviderError(
                "ollama",
                "request could not reach the provider.",
                retryable=True,
                kind="connection",
                fallback_allowed=True,
            ) from exc

        if not response.ok:
            raise self._http_error(
                response
            )

        try:
            data = response.json()
            answer = data[
                "message"
            ]["content"]

        except (
            ValueError,
            KeyError,
            TypeError,
        ) as exc:
            raise LLMProviderError(
                "ollama",
                "returned an unexpected response.",
                retryable=True,
                kind="response",
                fallback_allowed=True,
            ) from exc

        if not isinstance(answer, str):
            raise LLMProviderError(
                "ollama",
                "returned a non-text response.",
                retryable=True,
                kind="response",
                fallback_allowed=True,
            )

        cleaned_answer = answer.strip()

        if not cleaned_answer:
            raise LLMProviderError(
                "ollama",
                "returned an empty response.",
                retryable=True,
                kind="response",
                fallback_allowed=True,
            )

        return cleaned_answer
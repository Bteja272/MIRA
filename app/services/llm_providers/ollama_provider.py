from __future__ import annotations

from typing import Any

import requests

from app.core.config import settings
from app.services.llm_providers.base import (
    LLMProvider,
    LLMProviderError,
    LLMRequest,
)


class OllamaProvider(LLMProvider):
    """
    Local Ollama implementation of MIRA's LLM provider contract.
    """

    name = "ollama"

    def __init__(self) -> None:
        self.base_url = (
            settings
            .ollama_base_url
            .rstrip("/")
        )

        self.model_name = (
            settings
            .resolved_ollama_model_name
        )

    def generate(
        self,
        request: LLMRequest,
    ) -> str:
        url = (
            f"{self.base_url}/api/chat"
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

        # Local Ollama supports either plain JSON mode
        # or a complete JSON Schema in `format`.
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
                timeout=(
                    request.timeout_seconds
                ),
            )

        except requests.Timeout as exc:
            raise LLMProviderError(
                self.name,
                (
                    "request timed out after "
                    f"{request.timeout_seconds} seconds."
                ),
                retryable=True,
            ) from exc

        except requests.RequestException as exc:
            raise LLMProviderError(
                self.name,
                (
                    "could not connect to "
                    f"{url}: {exc}"
                ),
                retryable=True,
            ) from exc

        if not response.ok:
            retryable = (
                response.status_code == 429
                or response.status_code >= 500
            )

            raise LLMProviderError(
                self.name,
                (
                    "request failed with HTTP "
                    f"{response.status_code}: "
                    f"{response.text[:2000]}"
                ),
                retryable=retryable,
            )

        try:
            data = response.json()

            answer = (
                data["message"]["content"]
            )

        except (
            ValueError,
            KeyError,
            TypeError,
        ) as exc:
            raise LLMProviderError(
                self.name,
                (
                    "returned an unexpected response: "
                    f"{response.text[:2000]}"
                ),
            ) from exc

        if not isinstance(
            answer,
            str,
        ):
            raise LLMProviderError(
                self.name,
                "returned a non-text response.",
            )

        cleaned_answer = answer.strip()

        if not cleaned_answer:
            raise LLMProviderError(
                self.name,
                "returned an empty response.",
            )

        return cleaned_answer
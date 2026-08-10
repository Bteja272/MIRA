from __future__ import annotations

from typing import Any

import requests

from app.core.config import settings
from app.services.llm_providers.base import (
    LLMProvider,
    LLMProviderError,
    LLMRequest,
)


class GroqProvider(LLMProvider):
    """
    Groq implementation of MIRA's provider contract.

    Uses Groq's OpenAI-compatible REST endpoint directly so
    MIRA does not become coupled to a provider-specific SDK.
    """

    name = "groq"

    def __init__(self) -> None:
        api_key = (
            settings.groq_api_key.get_secret_value()
            if settings.groq_api_key is not None
            else ""
        ).strip()

        if not api_key:
            raise LLMProviderError(
                self.name,
                (
                    "GROQ_API_KEY is required "
                    "when Groq is selected."
                ),
            )

        self.api_key = api_key

        self.base_url = (
            settings
            .groq_base_url
            .rstrip("/")
        )

        self.model_name = (
            settings.groq_model_name
        )

    def generate(
        self,
        request: LLMRequest,
    ) -> str:
        url = (
            f"{self.base_url}"
            "/chat/completions"
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

        if request.temperature is not None:
            payload["temperature"] = (
                request.temperature
            )

        if (
            request.max_output_tokens
            is not None
        ):
            payload[
                "max_completion_tokens"
            ] = request.max_output_tokens

        # Batch 4B will begin using this for extraction.
        if request.json_schema is not None:
            payload["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": (
                        "mira_structured_response"
                    ),
                    "strict": True,
                    "schema": (
                        request.json_schema
                    ),
                },
            }

        elif request.json_mode:
            payload["response_format"] = {
                "type": "json_object",
            }

        headers = {
            "Authorization": (
                f"Bearer {self.api_key}"
            ),
            "Content-Type": (
                "application/json"
            ),
        }

        try:
            response = requests.post(
                url,
                headers=headers,
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
                data["choices"][0]
                ["message"]["content"]
            )

        except (
            ValueError,
            KeyError,
            IndexError,
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
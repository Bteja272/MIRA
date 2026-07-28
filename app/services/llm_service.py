from typing import Any

import requests

from app.core.config import settings


class LLMService:
    DEFAULT_SYSTEM_PROMPT = (
        "You are a helpful AI assistant."
    )

    @staticmethod
    def generate_response(
        prompt: str,
        system_prompt: str | None = None,
        timeout_seconds: int = 120,
        *,
        json_mode: bool = False,
        temperature: float | None = None,
        max_output_tokens: int | None = None,
        context_window: int | None = None,
        keep_alive: str | None = None,
    ) -> str:
        cleaned_prompt = prompt.strip()

        if not cleaned_prompt:
            raise ValueError(
                "prompt is required."
            )

        if timeout_seconds <= 0:
            raise ValueError(
                "timeout_seconds must be greater than zero."
            )

        if settings.llm_provider.lower() != "ollama":
            raise ValueError(
                "Unsupported LLM provider: "
                f"{settings.llm_provider}"
            )

        url = (
            f"{settings.ollama_base_url.rstrip('/')}"
            "/api/chat"
        )

        options: dict[str, Any] = {}

        if temperature is not None:
            options["temperature"] = temperature

        if max_output_tokens is not None:
            if max_output_tokens <= 0:
                raise ValueError(
                    "max_output_tokens must be greater than zero."
                )

            options["num_predict"] = (
                max_output_tokens
            )

        if context_window is not None:
            if context_window <= 0:
                raise ValueError(
                    "context_window must be greater than zero."
                )

            options["num_ctx"] = context_window

        payload: dict[str, Any] = {
            "model": settings.llm_model_name,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        system_prompt
                        or LLMService.DEFAULT_SYSTEM_PROMPT
                    ),
                },
                {
                    "role": "user",
                    "content": cleaned_prompt,
                },
            ],
            "stream": False,
        }

        if json_mode:
            payload["format"] = "json"

        if options:
            payload["options"] = options

        if keep_alive:
            payload["keep_alive"] = keep_alive

        try:
            response = requests.post(
                url,
                json=payload,
                timeout=timeout_seconds,
            )

        except requests.Timeout as exc:
            raise RuntimeError(
                "Ollama timed out after "
                f"{timeout_seconds} seconds."
            ) from exc

        except requests.RequestException as exc:
            raise RuntimeError(
                "Unable to connect to Ollama at "
                f"{url}: {exc}"
            ) from exc

        if not response.ok:
            raise RuntimeError(
                "Ollama request failed with HTTP "
                f"{response.status_code}: "
                f"{response.text[:2000]}"
            )

        try:
            data = response.json()
            answer = data["message"]["content"]

        except (
            ValueError,
            KeyError,
            TypeError,
        ) as exc:
            raise RuntimeError(
                "Unexpected Ollama response: "
                f"{response.text[:2000]}"
            ) from exc

        if not isinstance(answer, str):
            raise RuntimeError(
                "Ollama returned a non-text response."
            )

        cleaned_answer = answer.strip()

        if not cleaned_answer:
            raise RuntimeError(
                "Ollama returned an empty response."
            )

        return cleaned_answer
from __future__ import annotations

import logging
from typing import Any

from app.core.config import settings
from app.services.llm_providers import (
    LLMProviderFactory,
    LLMRequest,
)


logger = logging.getLogger(__name__)


class LLMService:
    """
    Provider-neutral LLM facade used throughout MIRA.

    Other MIRA services should depend on this class rather
    than directly depending on Groq or Ollama.
    """

    DEFAULT_SYSTEM_PROMPT = (
        "You are a helpful AI assistant."
    )

    @staticmethod
    def _validate_request(
        prompt: str,
        timeout_seconds: int,
        max_output_tokens: int | None,
        context_window: int | None,
    ) -> str:
        cleaned_prompt = prompt.strip()

        if not cleaned_prompt:
            raise ValueError(
                "prompt is required."
            )

        if timeout_seconds <= 0:
            raise ValueError(
                "timeout_seconds must be "
                "greater than zero."
            )

        if (
            max_output_tokens is not None
            and max_output_tokens <= 0
        ):
            raise ValueError(
                "max_output_tokens must be "
                "greater than zero."
            )

        if (
            context_window is not None
            and context_window <= 0
        ):
            raise ValueError(
                "context_window must be "
                "greater than zero."
            )

        return cleaned_prompt

    @classmethod
    def generate_response(
        cls,
        prompt: str,
        system_prompt: str | None = None,
        timeout_seconds: int = 120,
        *,
        json_mode: bool = False,
        temperature: float | None = None,
        max_output_tokens: int | None = None,
        context_window: int | None = None,
        keep_alive: str | None = None,
        json_schema: (
            dict[str, Any] | None
        ) = None,
    ) -> str:
        cleaned_prompt = (
            cls._validate_request(
                prompt=prompt,
                timeout_seconds=(
                    timeout_seconds
                ),
                max_output_tokens=(
                    max_output_tokens
                ),
                context_window=(
                    context_window
                ),
            )
        )

        request = LLMRequest(
            prompt=cleaned_prompt,
            system_prompt=(
                system_prompt
                or cls.DEFAULT_SYSTEM_PROMPT
            ),
            timeout_seconds=(
                timeout_seconds
            ),
            json_mode=json_mode,
            temperature=temperature,
            max_output_tokens=(
                max_output_tokens
            ),
            context_window=(
                context_window
            ),
            keep_alive=keep_alive,
            json_schema=json_schema,
        )

        primary_name = (
            settings
            .llm_provider
            .strip()
            .lower()
        )

        fallback_name = (
            settings
            .llm_fallback_provider
            .strip()
            .lower()
        )

        try:
            primary_provider = (
                LLMProviderFactory.create(
                    primary_name
                )
            )

            return (
                primary_provider.generate(
                    request
                )
            )

        except Exception as primary_exc:
            should_fallback = (
                bool(fallback_name)
                and fallback_name
                != primary_name
            )

            if not should_fallback:
                raise RuntimeError(
                    "LLM generation failed using "
                    f"{primary_name}: "
                    f"{primary_exc}"
                ) from primary_exc

            logger.warning(
                (
                    "llm_primary_provider_failed "
                    "primary=%s fallback=%s "
                    "error=%s"
                ),
                primary_name,
                fallback_name,
                str(primary_exc),
            )

            try:
                fallback_provider = (
                    LLMProviderFactory.create(
                        fallback_name
                    )
                )

                return (
                    fallback_provider.generate(
                        request
                    )
                )

            except Exception as fallback_exc:
                raise RuntimeError(
                    "LLM generation failed using "
                    f"primary provider "
                    f"{primary_name} and fallback "
                    f"provider {fallback_name}. "
                    f"Primary error: "
                    f"{primary_exc}. "
                    f"Fallback error: "
                    f"{fallback_exc}"
                ) from fallback_exc
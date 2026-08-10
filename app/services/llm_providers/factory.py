from __future__ import annotations

from app.services.llm_providers.base import (
    LLMProvider,
)
from app.services.llm_providers.groq_provider import (
    GroqProvider,
)
from app.services.llm_providers.ollama_provider import (
    OllamaProvider,
)


class LLMProviderFactory:
    """
    Convert a configured provider name into its implementation.
    """

    SUPPORTED_PROVIDERS = {
        "groq",
        "ollama",
    }

    @classmethod
    def create(
        cls,
        provider_name: str,
    ) -> LLMProvider:
        normalized = (
            provider_name
            .strip()
            .lower()
        )

        if normalized == "ollama":
            return OllamaProvider()

        if normalized == "groq":
            return GroqProvider()

        raise ValueError(
            "Unsupported LLM provider: "
            f"{provider_name}. "
            "Supported providers: "
            + ", ".join(
                sorted(
                    cls.SUPPORTED_PROVIDERS
                )
            )
        )
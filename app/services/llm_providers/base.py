from __future__ import annotations

from abc import (
    ABC,
    abstractmethod,
)
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class LLMRequest:
    """
    Provider-neutral generation request.

    Providers translate these generic fields into their
    own API-specific request formats.
    """

    prompt: str
    system_prompt: str
    timeout_seconds: int

    json_mode: bool = False
    temperature: float | None = None
    max_output_tokens: int | None = None

    # Primarily useful for local Ollama.
    context_window: int | None = None
    keep_alive: str | None = None

    # Used for providers that support schema-constrained output.
    json_schema: dict[str, Any] | None = None


class LLMProviderError(RuntimeError):
    """
    Normalized error raised by every LLM provider.

    This prevents the rest of MIRA from depending on
    provider-specific exception classes.
    """

    def __init__(
        self,
        provider: str,
        message: str,
        *,
        retryable: bool = False,
    ) -> None:
        super().__init__(
            f"{provider}: {message}"
        )

        self.provider = provider
        self.retryable = retryable


class LLMProvider(ABC):
    """
    Contract every MIRA LLM provider must implement.
    """

    name: str

    @abstractmethod
    def generate(
        self,
        request: LLMRequest,
    ) -> str:
        raise NotImplementedError
from abc import (
    ABC,
    abstractmethod,
)
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class LLMRequest:
    prompt: str
    system_prompt: str
    timeout_seconds: int
    json_mode: bool = False
    temperature: float | None = None
    max_output_tokens: int | None = None
    context_window: int | None = None
    keep_alive: str | None = None
    json_schema: dict[str, Any] | None = None


class LLMProviderError(RuntimeError):
    """
    Normalized provider failure.

    retryable:
        The same provider may reasonably succeed if retried.

    fallback_allowed:
        MIRA may move to the configured fallback provider after the
        current provider's retry budget is exhausted.

    kind:
        A stable machine-readable category used for policy and logs.

    The error message must never contain prompts, raw model responses,
    API keys, or provider payloads that may contain user information.
    """

    def __init__(
        self,
        provider: str,
        message: str,
        retryable: bool = False,
        *,
        kind: str = "provider",
        status_code: int | None = None,
        error_code: str | None = None,
        fallback_allowed: bool = True,
        retry_after_seconds: float | None = None,
    ) -> None:
        self.provider = provider.strip().lower()
        self.message = message.strip()
        self.retryable = retryable
        self.kind = kind.strip().lower()
        self.status_code = status_code
        self.error_code = (
            error_code.strip()
            if isinstance(error_code, str)
            and error_code.strip()
            else None
        )
        self.fallback_allowed = fallback_allowed
        self.retry_after_seconds = (
            retry_after_seconds
            if (
                retry_after_seconds is not None
                and retry_after_seconds >= 0
            )
            else None
        )

        super().__init__(
            f"{self.provider}: {self.message}"
        )


class LLMProvider(ABC):
    name: str

    @property
    @abstractmethod
    def model_name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def generate(
        self,
        request: LLMRequest,
    ) -> str:
        raise NotImplementedError
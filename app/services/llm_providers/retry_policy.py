from dataclasses import dataclass

from pydantic import (
    Field,
)
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)

from app.services.llm_providers.base import (
    LLMProviderError,
)


class _LLMRetrySettings(
    BaseSettings
):
    llm_provider_max_retries: int = Field(
        default=1,
        ge=0,
        le=5,
    )
    llm_provider_retry_base_delay_seconds: float = (
        Field(
            default=0.25,
            ge=0.0,
            le=30.0,
        )
    )
    llm_provider_retry_max_delay_seconds: float = (
        Field(
            default=2.0,
            ge=0.0,
            le=60.0,
        )
    )
    llm_provider_retry_after_cap_seconds: float = (
        Field(
            default=5.0,
            ge=0.0,
            le=120.0,
        )
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )


@dataclass(frozen=True)
class LLMRetryPolicy:
    """
    Small bounded retry policy for hosted/local LLM providers.

    Defaults intentionally allow only one retry. LLM requests can be
    expensive, so MIRA avoids long retry storms before falling back.
    """

    max_retries: int = 1
    base_delay_seconds: float = 0.25
    max_delay_seconds: float = 2.0
    retry_after_cap_seconds: float = 5.0

    @classmethod
    def from_environment(
        cls,
    ) -> "LLMRetryPolicy":
        retry_settings = (
            _LLMRetrySettings()
        )

        return cls(
            max_retries=(
                retry_settings
                .llm_provider_max_retries
            ),
            base_delay_seconds=(
                retry_settings
                .llm_provider_retry_base_delay_seconds
            ),
            max_delay_seconds=(
                retry_settings
                .llm_provider_retry_max_delay_seconds
            ),
            retry_after_cap_seconds=(
                retry_settings
                .llm_provider_retry_after_cap_seconds
            ),
        )

    def delay_seconds(
        self,
        *,
        retry_number: int,
        error: LLMProviderError,
    ) -> float:
        if retry_number <= 0:
            raise ValueError(
                "retry_number must be greater than zero."
            )

        if (
            error.retry_after_seconds
            is not None
        ):
            return min(
                error.retry_after_seconds,
                self.retry_after_cap_seconds,
            )

        exponential_delay = (
            self.base_delay_seconds
            * (2 ** (retry_number - 1))
        )

        return min(
            exponential_delay,
            self.max_delay_seconds,
        )
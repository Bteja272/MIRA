import logging
import time
from dataclasses import dataclass
from time import perf_counter
from typing import Any

from app.core.config import settings
from app.services.llm_providers.base import (
    LLMProviderError,
    LLMRequest,
)
from app.services.llm_providers.factory import (
    LLMProviderFactory,
)
from app.services.llm_providers.retry_policy import (
    LLMRetryPolicy,
)


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class LLMGenerationMetadata:
    primary_provider: str
    provider: str
    model: str
    attempts: int
    fallback_used: bool
    total_latency_ms: float


@dataclass(frozen=True)
class LLMGenerationResult:
    text: str
    metadata: LLMGenerationMetadata


@dataclass(frozen=True)
class _ProviderRunResult:
    text: str
    provider: str
    model: str
    attempts: int


class _ProviderRunFailure(RuntimeError):
    def __init__(
        self,
        *,
        provider: str,
        model: str,
        attempts: int,
        error: LLMProviderError,
    ) -> None:
        self.provider = provider
        self.model = model
        self.attempts = attempts
        self.error = error
        super().__init__(str(error))


class LLMService:
    DEFAULT_SYSTEM_PROMPT = (
        "You are a helpful AI assistant."
    )

    @staticmethod
    def _normalize_provider_name(
        provider_name: str | None,
    ) -> str:
        if provider_name is None:
            return ""

        return provider_name.strip().lower()

    @staticmethod
    def _provider_model_name(
        provider: Any,
    ) -> str:
        model_name = getattr(
            provider,
            "model_name",
            "",
        )

        if isinstance(
            model_name,
            str,
        ):
            return model_name.strip()

        return ""

    @classmethod
    def _run_provider(
        cls,
        *,
        provider_name: str,
        request: LLMRequest,
        retry_policy: LLMRetryPolicy,
    ) -> _ProviderRunResult:
        provider = (
            LLMProviderFactory.create(
                provider_name
            )
        )

        model_name = (
            cls._provider_model_name(
                provider
            )
        )

        total_attempts = (
            retry_policy.max_retries + 1
        )

        for attempt in range(
            1,
            total_attempts + 1,
        ):
            attempt_started_at = (
                perf_counter()
            )

            try:
                answer = provider.generate(
                    request
                )

            except LLMProviderError as exc:
                attempt_ms = (
                    perf_counter()
                    - attempt_started_at
                ) * 1000

                logger.warning(
                    "llm_provider_attempt_failed "
                    "provider=%s model=%s "
                    "attempt=%s latency_ms=%.3f "
                    "kind=%s status_code=%s "
                    "error_code=%s retryable=%s "
                    "fallback_allowed=%s",
                    provider_name,
                    model_name or "unknown",
                    attempt,
                    attempt_ms,
                    exc.kind,
                    exc.status_code,
                    exc.error_code,
                    exc.retryable,
                    exc.fallback_allowed,
                )

                can_retry = (
                    exc.retryable
                    and attempt
                    < total_attempts
                )

                if can_retry:
                    retry_number = attempt
                    delay_seconds = (
                        retry_policy
                        .delay_seconds(
                            retry_number=(
                                retry_number
                            ),
                            error=exc,
                        )
                    )

                    logger.info(
                        "llm_provider_retry "
                        "provider=%s model=%s "
                        "retry_number=%s "
                        "delay_seconds=%.3f "
                        "kind=%s",
                        provider_name,
                        model_name or "unknown",
                        retry_number,
                        delay_seconds,
                        exc.kind,
                    )

                    if delay_seconds > 0:
                        time.sleep(
                            delay_seconds
                        )

                    continue

                raise _ProviderRunFailure(
                    provider=provider_name,
                    model=model_name,
                    attempts=attempt,
                    error=exc,
                ) from exc

            except Exception as exc:
                attempt_ms = (
                    perf_counter()
                    - attempt_started_at
                ) * 1000

                logger.error(
                    "llm_provider_unexpected_failure "
                    "provider=%s model=%s "
                    "attempt=%s latency_ms=%.3f",
                    provider_name,
                    model_name or "unknown",
                    attempt,
                    attempt_ms,
                )

                normalized_error = (
                    LLMProviderError(
                        provider_name,
                        "unexpected provider failure.",
                        retryable=False,
                        kind="unexpected",
                        fallback_allowed=True,
                    )
                )

                raise _ProviderRunFailure(
                    provider=provider_name,
                    model=model_name,
                    attempts=attempt,
                    error=normalized_error,
                ) from exc

            attempt_ms = (
                perf_counter()
                - attempt_started_at
            ) * 1000

            logger.info(
                "llm_provider_attempt_completed "
                "provider=%s model=%s "
                "attempt=%s latency_ms=%.3f",
                provider_name,
                model_name or "unknown",
                attempt,
                attempt_ms,
            )

            return _ProviderRunResult(
                text=answer,
                provider=provider_name,
                model=model_name,
                attempts=attempt,
            )

        raise RuntimeError(
            "Provider retry loop terminated "
            "unexpectedly."
        )

    @classmethod
    def _generate(
        cls,
        *,
        request: LLMRequest,
    ) -> LLMGenerationResult:
        started_at = perf_counter()

        primary_provider = (
            cls._normalize_provider_name(
                settings.llm_provider
            )
        )

        fallback_provider = (
            cls._normalize_provider_name(
                getattr(
                    settings,
                    "llm_fallback_provider",
                    "",
                )
            )
        )

        if not primary_provider:
            raise ValueError(
                "LLM_PROVIDER is required."
            )

        retry_policy = (
            LLMRetryPolicy
            .from_environment()
        )

        try:
            primary_result = (
                cls._run_provider(
                    provider_name=(
                        primary_provider
                    ),
                    request=request,
                    retry_policy=(
                        retry_policy
                    ),
                )
            )

        except _ProviderRunFailure as exc:
            fallback_is_usable = (
                bool(fallback_provider)
                and fallback_provider
                != primary_provider
                and exc.error
                .fallback_allowed
            )

            if not fallback_is_usable:
                logger.error(
                    "llm_generation_failed "
                    "primary=%s kind=%s "
                    "status_code=%s "
                    "error_code=%s "
                    "fallback_used=false",
                    primary_provider,
                    exc.error.kind,
                    exc.error.status_code,
                    exc.error.error_code,
                )

                raise RuntimeError(
                    "LLM generation failed using "
                    f"{primary_provider}."
                ) from exc

            logger.warning(
                "llm_primary_provider_failed "
                "primary=%s fallback=%s "
                "kind=%s status_code=%s "
                "error_code=%s "
                "attempts=%s",
                primary_provider,
                fallback_provider,
                exc.error.kind,
                exc.error.status_code,
                exc.error.error_code,
                exc.attempts,
            )

            try:
                fallback_result = (
                    cls._run_provider(
                        provider_name=(
                            fallback_provider
                        ),
                        request=request,
                        retry_policy=(
                            retry_policy
                        ),
                    )
                )

            except _ProviderRunFailure as fallback_exc:
                logger.error(
                    "llm_fallback_provider_failed "
                    "primary=%s fallback=%s "
                    "kind=%s status_code=%s "
                    "error_code=%s "
                    "attempts=%s",
                    primary_provider,
                    fallback_provider,
                    fallback_exc.error.kind,
                    fallback_exc.error.status_code,
                    fallback_exc.error.error_code,
                    fallback_exc.attempts,
                )

                raise RuntimeError(
                    "LLM generation failed using "
                    f"primary {primary_provider} "
                    "and fallback "
                    f"{fallback_provider}."
                ) from fallback_exc

            total_latency_ms = (
                perf_counter()
                - started_at
            ) * 1000

            total_attempts = (
                exc.attempts
                + fallback_result.attempts
            )

            metadata = (
                LLMGenerationMetadata(
                    primary_provider=(
                        primary_provider
                    ),
                    provider=(
                        fallback_result
                        .provider
                    ),
                    model=(
                        fallback_result
                        .model
                    ),
                    attempts=total_attempts,
                    fallback_used=True,
                    total_latency_ms=(
                        total_latency_ms
                    ),
                )
            )

            logger.info(
                "llm_generation_completed "
                "primary=%s provider=%s "
                "model=%s attempts=%s "
                "fallback_used=true "
                "latency_ms=%.3f",
                metadata.primary_provider,
                metadata.provider,
                metadata.model
                or "unknown",
                metadata.attempts,
                metadata.total_latency_ms,
            )

            return LLMGenerationResult(
                text=fallback_result.text,
                metadata=metadata,
            )

        total_latency_ms = (
            perf_counter()
            - started_at
        ) * 1000

        metadata = LLMGenerationMetadata(
            primary_provider=(
                primary_provider
            ),
            provider=(
                primary_result.provider
            ),
            model=primary_result.model,
            attempts=(
                primary_result.attempts
            ),
            fallback_used=False,
            total_latency_ms=(
                total_latency_ms
            ),
        )

        logger.info(
            "llm_generation_completed "
            "primary=%s provider=%s "
            "model=%s attempts=%s "
            "fallback_used=false "
            "latency_ms=%.3f",
            metadata.primary_provider,
            metadata.provider,
            metadata.model
            or "unknown",
            metadata.attempts,
            metadata.total_latency_ms,
        )

        return LLMGenerationResult(
            text=primary_result.text,
            metadata=metadata,
        )

    @classmethod
    def generate_response_with_metadata(
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
    ) -> LLMGenerationResult:
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
            max_output_tokens
            is not None
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

        return cls._generate(
            request=request
        )

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
        result = (
            cls.generate_response_with_metadata(
                prompt=prompt,
                system_prompt=(
                    system_prompt
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
        )

        return result.text
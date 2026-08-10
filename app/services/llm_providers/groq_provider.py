from typing import Any

import requests

from app.core.config import settings
from app.services.llm_providers.base import (
    LLMProvider,
    LLMProviderError,
    LLMRequest,
)


class GroqProvider(LLMProvider):
    name = "groq"

    @property
    def model_name(self) -> str:
        return settings.groq_model_name

    @staticmethod
    def _api_key() -> str:
        secret = settings.groq_api_key

        if secret is None:
            raise LLMProviderError(
                "groq",
                "GROQ_API_KEY is not configured.",
                retryable=False,
                kind="configuration",
                fallback_allowed=False,
            )

        try:
            value = secret.get_secret_value()
        except AttributeError:
            value = str(secret)

        cleaned_value = value.strip()

        if not cleaned_value:
            raise LLMProviderError(
                "groq",
                "GROQ_API_KEY is not configured.",
                retryable=False,
                kind="configuration",
                fallback_allowed=False,
            )

        return cleaned_value

    @staticmethod
    def _retry_after_seconds(
        response: requests.Response,
    ) -> float | None:
        raw_value = response.headers.get(
            "retry-after"
        )

        if raw_value is None:
            return None

        try:
            value = float(raw_value)
        except (TypeError, ValueError):
            return None

        return value if value >= 0 else None

    @staticmethod
    def _safe_error_details(
        response: requests.Response,
    ) -> tuple[str | None, str]:
        """
        Extract only provider error metadata.

        Deliberately ignores `failed_generation` because it can contain
        generated medical-document content and must not leak into logs.
        """
        error_code: str | None = None
        message = "request failed"

        try:
            payload = response.json()
        except ValueError:
            payload = None

        if isinstance(payload, dict):
            error = payload.get("error")

            if isinstance(error, dict):
                raw_code = error.get("code")
                raw_message = error.get("message")

                if isinstance(
                    raw_code,
                    str,
                ) and raw_code.strip():
                    error_code = raw_code.strip()

                if isinstance(
                    raw_message,
                    str,
                ) and raw_message.strip():
                    message = raw_message.strip()

            elif isinstance(error, str):
                if error.strip():
                    message = error.strip()

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

        return (
            error_code,
            message[:1000],
        )

    @classmethod
    def _http_error(
        cls,
        response: requests.Response,
    ) -> LLMProviderError:
        status_code = int(
            response.status_code
        )
        (
            error_code,
            provider_message,
        ) = cls._safe_error_details(
            response
        )

        common_message = (
            f"request failed with HTTP "
            f"{status_code}: "
            f"{provider_message}"
        )

        if (
            status_code == 400
            and error_code
            == "json_validate_failed"
        ):
            return LLMProviderError(
                "groq",
                common_message,
                retryable=True,
                kind="structured_output",
                status_code=status_code,
                error_code=error_code,
                fallback_allowed=False,
            )

        if status_code in {
            408,
            422,
        }:
            return LLMProviderError(
                "groq",
                common_message,
                retryable=True,
                kind=(
                    "timeout"
                    if status_code == 408
                    else "unprocessable"
                ),
                status_code=status_code,
                error_code=error_code,
                fallback_allowed=(
                    status_code == 408
                ),
            )

        if status_code == 429:
            return LLMProviderError(
                "groq",
                common_message,
                retryable=True,
                kind="rate_limit",
                status_code=status_code,
                error_code=error_code,
                fallback_allowed=True,
                retry_after_seconds=(
                    cls._retry_after_seconds(
                        response
                    )
                ),
            )

        if status_code == 498:
            return LLMProviderError(
                "groq",
                common_message,
                retryable=True,
                kind="capacity",
                status_code=status_code,
                error_code=error_code,
                fallback_allowed=True,
            )

        if status_code in {
            500,
            502,
            503,
            504,
        }:
            return LLMProviderError(
                "groq",
                common_message,
                retryable=True,
                kind="server",
                status_code=status_code,
                error_code=error_code,
                fallback_allowed=True,
            )

        if status_code in {
            401,
            403,
        }:
            return LLMProviderError(
                "groq",
                common_message,
                retryable=False,
                kind="authentication",
                status_code=status_code,
                error_code=error_code,
                fallback_allowed=False,
            )

        if status_code == 404:
            return LLMProviderError(
                "groq",
                common_message,
                retryable=False,
                kind="configuration",
                status_code=status_code,
                error_code=error_code,
                fallback_allowed=False,
            )

        return LLMProviderError(
            "groq",
            common_message,
            retryable=False,
            kind="request",
            status_code=status_code,
            error_code=error_code,
            fallback_allowed=False,
        )

    def generate(
        self,
        request: LLMRequest,
    ) -> str:
        api_key = self._api_key()

        url = (
            f"{settings.groq_base_url.rstrip('/')}"
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

        try:
            response = requests.post(
                url,
                headers={
                    "Authorization": (
                        f"Bearer {api_key}"
                    ),
                    "Content-Type": (
                        "application/json"
                    ),
                },
                json=payload,
                timeout=request.timeout_seconds,
            )

        except requests.Timeout as exc:
            raise LLMProviderError(
                "groq",
                "request timed out.",
                retryable=True,
                kind="timeout",
                fallback_allowed=True,
            ) from exc

        except requests.RequestException as exc:
            raise LLMProviderError(
                "groq",
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
                "groq",
                "returned an unexpected response.",
                retryable=True,
                kind="response",
                fallback_allowed=True,
            ) from exc

        if not isinstance(answer, str):
            raise LLMProviderError(
                "groq",
                "returned a non-text response.",
                retryable=True,
                kind="response",
                fallback_allowed=True,
            )

        cleaned_answer = answer.strip()

        if not cleaned_answer:
            raise LLMProviderError(
                "groq",
                "returned an empty response.",
                retryable=True,
                kind="response",
                fallback_allowed=True,
            )

        return cleaned_answer
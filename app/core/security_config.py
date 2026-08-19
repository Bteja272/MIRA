from __future__ import annotations

from pydantic import (
    field_validator,
    model_validator,
)
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


class SecuritySettings(BaseSettings):
    # Refresh/session lifetime.
    refresh_token_expire_days: int = 7

    # Cookie names.
    access_cookie_name: str = (
        "mira_access"
    )
    refresh_cookie_name: str = (
        "mira_refresh"
    )
    csrf_cookie_name: str = (
        "mira_csrf"
    )
    csrf_header_name: str = (
        "X-CSRF-Token"
    )

    # Browser cookie settings.
    cookie_secure: bool = False
    cookie_samesite: str = "lax"
    cookie_domain: str | None = None

    # JWT metadata.
    jwt_issuer: str = "mira-api"
    jwt_audience: str = "mira-web"

    # CSRF.
    csrf_enabled: bool = True

    # Rate limiting.
    rate_limit_enabled: bool = True

    rate_limit_general_requests: int = (
        240
    )
    rate_limit_general_window_seconds: int = (
        60
    )

    rate_limit_login_requests: int = (
        10
    )
    rate_limit_login_window_seconds: int = (
        900
    )

    rate_limit_register_requests: int = (
        5
    )
    rate_limit_register_window_seconds: int = (
        3600
    )

    rate_limit_refresh_requests: int = (
        30
    )
    rate_limit_refresh_window_seconds: int = (
        900
    )

    # Browser/API hardening.
    expose_api_docs: bool = True
    hsts_enabled: bool = False

    trusted_hosts: list[str] = [
        "localhost",
        "127.0.0.1",
        "testserver",
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    @field_validator(
        "cookie_samesite",
        mode="before",
    )
    @classmethod
    def normalize_samesite(
        cls,
        value,
    ) -> str:
        cleaned = (
            str(value)
            .strip()
            .lower()
        )

        if cleaned not in {
            "lax",
            "strict",
            "none",
        }:
            raise ValueError(
                "cookie_samesite must be "
                "lax, strict, or none."
            )

        return cleaned

    @field_validator(
        "trusted_hosts",
        mode="before",
    )
    @classmethod
    def normalize_trusted_hosts(
        cls,
        value,
    ):
        if isinstance(value, str):
            return [
                item.strip()
                for item in value.split(",")
                if item.strip()
            ]

        return value

    @model_validator(mode="after")
    def validate_security_settings(
        self,
    ):
        positive_fields = {
            "refresh_token_expire_days": (
                self.refresh_token_expire_days
            ),
            "rate_limit_general_requests": (
                self.rate_limit_general_requests
            ),
            "rate_limit_general_window_seconds": (
                self.rate_limit_general_window_seconds
            ),
            "rate_limit_login_requests": (
                self.rate_limit_login_requests
            ),
            "rate_limit_login_window_seconds": (
                self.rate_limit_login_window_seconds
            ),
            "rate_limit_register_requests": (
                self.rate_limit_register_requests
            ),
            "rate_limit_register_window_seconds": (
                self.rate_limit_register_window_seconds
            ),
            "rate_limit_refresh_requests": (
                self.rate_limit_refresh_requests
            ),
            "rate_limit_refresh_window_seconds": (
                self.rate_limit_refresh_window_seconds
            ),
        }

        for field_name, value in (
            positive_fields.items()
        ):
            if value <= 0:
                raise ValueError(
                    f"{field_name} must be "
                    "greater than zero."
                )

        if (
            self.cookie_samesite == "none"
            and not self.cookie_secure
        ):
            raise ValueError(
                "SameSite=None cookies require "
                "COOKIE_SECURE=true."
            )

        return self


security_settings = SecuritySettings()
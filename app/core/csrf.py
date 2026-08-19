import hmac

from fastapi import Request

from app.core.config import settings
from app.core.security_config import (
    security_settings,
)


SAFE_METHODS = {
    "GET",
    "HEAD",
    "OPTIONS",
}


CSRF_BOOTSTRAP_PATHS = {
    "/auth/login",
    "/auth/register",
}


def validate_csrf_tokens(
    *,
    cookie_token: str | None,
    header_token: str | None,
) -> bool:
    if (
        not cookie_token
        or not header_token
    ):
        return False

    return hmac.compare_digest(
        cookie_token,
        header_token,
    )


def request_uses_cookie_auth(
    request: Request,
) -> bool:
    return bool(
        request.cookies.get(
            security_settings
            .access_cookie_name
        )
        or request.cookies.get(
            security_settings
            .refresh_cookie_name
        )
    )


def origin_is_allowed(
    request: Request,
) -> bool:
    origin = request.headers.get(
        "origin"
    )

    # Non-browser clients may not send Origin.
    if not origin:
        return True

    normalized = origin.rstrip(
        "/"
    )

    return (
        normalized
        in settings.cors_allowed_origins
    )


def csrf_is_valid(
    request: Request,
) -> bool:
    if not (
        security_settings.csrf_enabled
    ):
        return True

    method = request.method.upper()

    if method in SAFE_METHODS:
        return True

    if not origin_is_allowed(
        request
    ):
        return False

    if (
        request.url.path
        in CSRF_BOOTSTRAP_PATHS
    ):
        return True

    # Bearer-only/API clients do not rely
    # on automatically attached cookies.
    if not request_uses_cookie_auth(
        request
    ):
        return True

    cookie_token = (
        request.cookies.get(
            security_settings
            .csrf_cookie_name
        )
    )

    header_token = (
        request.headers.get(
            security_settings
            .csrf_header_name
        )
    )

    return validate_csrf_tokens(
        cookie_token=cookie_token,
        header_token=header_token,
    )
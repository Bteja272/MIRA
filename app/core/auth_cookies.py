from fastapi import Response

from app.core.config import settings
from app.core.security_config import (
    security_settings,
)


def set_auth_cookies(
    *,
    response: Response,
    access_token: str,
    refresh_token: str,
    csrf_token: str,
) -> None:
    access_max_age = (
        settings
        .access_token_expire_minutes
        * 60
    )

    refresh_max_age = (
        security_settings
        .refresh_token_expire_days
        * 24
        * 60
        * 60
    )

    common = {
        "secure": (
            security_settings
            .cookie_secure
        ),
        "samesite": (
            security_settings
            .cookie_samesite
        ),
        "domain": (
            security_settings
            .cookie_domain
        ),
    }

    response.set_cookie(
        key=(
            security_settings
            .access_cookie_name
        ),
        value=access_token,
        max_age=access_max_age,
        httponly=True,
        path="/",
        **common,
    )

    response.set_cookie(
        key=(
            security_settings
            .refresh_cookie_name
        ),
        value=refresh_token,
        max_age=refresh_max_age,
        httponly=True,
        path="/auth",
        **common,
    )

    # Deliberately readable by JavaScript.
    # The frontend echoes this value in
    # X-CSRF-Token for unsafe requests.
    response.set_cookie(
        key=(
            security_settings
            .csrf_cookie_name
        ),
        value=csrf_token,
        max_age=refresh_max_age,
        httponly=False,
        path="/",
        **common,
    )


def clear_auth_cookies(
    response: Response,
) -> None:
    common = {
        "secure": (
            security_settings
            .cookie_secure
        ),
        "samesite": (
            security_settings
            .cookie_samesite
        ),
        "domain": (
            security_settings
            .cookie_domain
        ),
    }

    response.delete_cookie(
        key=(
            security_settings
            .access_cookie_name
        ),
        path="/",
        **common,
    )

    response.delete_cookie(
        key=(
            security_settings
            .refresh_cookie_name
        ),
        path="/auth",
        **common,
    )

    response.delete_cookie(
        key=(
            security_settings
            .csrf_cookie_name
        ),
        path="/",
        **common,
    )
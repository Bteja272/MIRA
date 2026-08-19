from __future__ import annotations

import hashlib
import secrets
from datetime import (
    datetime,
    timedelta,
    timezone,
)

import jwt
from jwt import InvalidTokenError
from pwdlib import PasswordHash

from app.core.config import settings
from app.core.security_config import (
    security_settings,
)


password_hash = PasswordHash.recommended()


class TokenValidationError(Exception):
    pass


def hash_password(
    password: str,
) -> str:
    return password_hash.hash(
        password
    )


def verify_password(
    plain_password: str,
    stored_password_hash: str,
) -> bool:
    try:
        return password_hash.verify(
            plain_password,
            stored_password_hash,
        )
    except Exception:
        return False


def _jwt_secret() -> str:
    return (
        settings.jwt_secret_key
        .get_secret_value()
    )


def _base_payload(
    *,
    user_id: str,
    token_type: str,
    issued_at: datetime,
    expires_at: datetime,
) -> dict:
    return {
        "sub": user_id,
        "type": token_type,
        "iss": (
            security_settings.jwt_issuer
        ),
        "aud": (
            security_settings.jwt_audience
        ),
        "iat": issued_at,
        "exp": expires_at,
    }


def create_access_token(
    user_id: str,
) -> str:
    issued_at = datetime.now(
        timezone.utc
    )

    expires_at = (
        issued_at
        + timedelta(
            minutes=(
                settings
                .access_token_expire_minutes
            )
        )
    )

    payload = _base_payload(
        user_id=user_id,
        token_type="access",
        issued_at=issued_at,
        expires_at=expires_at,
    )

    return jwt.encode(
        payload,
        _jwt_secret(),
        algorithm=(
            settings.jwt_algorithm
        ),
    )


def create_refresh_token(
    *,
    user_id: str,
    session_id: str,
) -> str:
    issued_at = datetime.now(
        timezone.utc
    )

    expires_at = (
        issued_at
        + timedelta(
            days=(
                security_settings
                .refresh_token_expire_days
            )
        )
    )

    payload = _base_payload(
        user_id=user_id,
        token_type="refresh",
        issued_at=issued_at,
        expires_at=expires_at,
    )

    payload["jti"] = session_id

    return jwt.encode(
        payload,
        _jwt_secret(),
        algorithm=(
            settings.jwt_algorithm
        ),
    )


def _decode_token(
    token: str,
    *,
    expected_type: str,
) -> dict:
    try:
        payload = jwt.decode(
            token,
            _jwt_secret(),
            algorithms=[
                settings.jwt_algorithm
            ],
            audience=(
                security_settings
                .jwt_audience
            ),
            issuer=(
                security_settings
                .jwt_issuer
            ),
            options={
                "require": [
                    "sub",
                    "type",
                    "iss",
                    "aud",
                    "iat",
                    "exp",
                ],
            },
        )

    except InvalidTokenError as exc:
        raise TokenValidationError(
            "Invalid authentication token."
        ) from exc

    token_type = payload.get(
        "type"
    )

    if token_type != expected_type:
        raise TokenValidationError(
            "Unexpected authentication "
            "token type."
        )

    user_id = payload.get(
        "sub"
    )

    if (
        not isinstance(
            user_id,
            str,
        )
        or not user_id.strip()
    ):
        raise TokenValidationError(
            "Authentication token does "
            "not contain a valid user ID."
        )

    return payload


def decode_access_token(
    token: str,
) -> str:
    payload = _decode_token(
        token,
        expected_type="access",
    )

    return str(
        payload["sub"]
    )


def decode_refresh_token(
    token: str,
) -> tuple[str, str]:
    payload = _decode_token(
        token,
        expected_type="refresh",
    )

    session_id = payload.get(
        "jti"
    )

    if (
        not isinstance(
            session_id,
            str,
        )
        or not session_id.strip()
    ):
        raise TokenValidationError(
            "Refresh token does not "
            "contain a valid session ID."
        )

    return (
        str(payload["sub"]),
        session_id,
    )


def hash_token(
    token: str,
) -> str:
    return hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()


def generate_csrf_token() -> str:
    return secrets.token_urlsafe(
        32
    )
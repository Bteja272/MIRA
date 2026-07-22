from datetime import (
    datetime,
    timedelta,
    timezone,
)

import jwt
from jwt import InvalidTokenError
from pwdlib import PasswordHash

from app.core.config import settings


password_hash = (
    PasswordHash.recommended()
)


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

    payload = {
        "sub": user_id,
        "type": "access",
        "iat": issued_at,
        "exp": expires_at,
    }

    return jwt.encode(
        payload,
        settings.jwt_secret_key.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )


def decode_access_token(
    token: str,
) -> str:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key.get_secret_value(),
            algorithms=[
                settings.jwt_algorithm
            ],
            options={
                "require": [
                    "sub",
                    "type",
                    "iat",
                    "exp",
                ]
            },
        )

    except InvalidTokenError as exc:
        raise TokenValidationError(
            "Invalid or expired access token."
        ) from exc

    if payload.get("type") != "access":
        raise TokenValidationError(
            "Invalid token type."
        )

    user_id = payload.get("sub")

    if (
        not isinstance(user_id, str)
        or not user_id.strip()
    ):
        raise TokenValidationError(
            "Token subject is missing."
        )

    return user_id
from typing import Annotated

from fastapi import (
    Depends,
    HTTPException,
    status,
)
from fastapi.security import (
    OAuth2PasswordBearer,
)

from app.core.security import (
    TokenValidationError,
    decode_access_token,
)
from app.db.models import User
from app.services.user_service import (
    UserService,
)


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login"
)


def _credentials_exception() -> HTTPException:
    return HTTPException(
        status_code=(
            status.HTTP_401_UNAUTHORIZED
        ),
        detail=(
            "Could not validate credentials."
        ),
        headers={
            "WWW-Authenticate": "Bearer"
        },
    )


def get_current_user(
    token: Annotated[
        str,
        Depends(oauth2_scheme),
    ],
) -> User:
    try:
        user_id = decode_access_token(
            token
        )

    except TokenValidationError as exc:
        raise _credentials_exception() from exc

    user = UserService.get_by_user_id(
        user_id
    )

    if (
        user is None
        or not user.is_active
    ):
        raise _credentials_exception()

    return user


CurrentUser = Annotated[
    User,
    Depends(get_current_user),
]
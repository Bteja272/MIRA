from typing import (
    Annotated,
)

from fastapi import (
    Depends,
    HTTPException,
    Request,
    status,
)
from fastapi.security import (
    OAuth2PasswordBearer,
)

from app.core.security import (
    TokenValidationError,
    decode_access_token,
)
from app.core.security_config import (
    security_settings,
)
from app.db.models import User
from app.services.user_service import (
    UserService,
)


oauth2_scheme = (
    OAuth2PasswordBearer(
        tokenUrl="/auth/login",
        auto_error=False,
    )
)


def _credentials_exception():
    return HTTPException(
        status_code=(
            status.HTTP_401_UNAUTHORIZED
        ),
        detail=(
            "Could not validate "
            "credentials."
        ),
        headers={
            "WWW-Authenticate": "Bearer",
        },
    )


def get_current_user(
    request: Request,
    bearer_token: Annotated[
        str | None,
        Depends(oauth2_scheme),
    ] = None,
) -> User:
    cookie_token = (
        request.cookies.get(
            security_settings
            .access_cookie_name
        )
    )

    token = (
        cookie_token
        or bearer_token
    )

    if not token:
        raise _credentials_exception()

    try:
        user_id = (
            decode_access_token(
                token
            )
        )

    except TokenValidationError:
        raise _credentials_exception()

    user = (
        UserService.get_by_user_id(
            user_id
        )
    )

    if (
        user is None
        or not user.is_active
    ):
        raise _credentials_exception()

    request.state.user_id = (
        user.user_id
    )

    return user


CurrentUser = Annotated[
    User,
    Depends(get_current_user),
]
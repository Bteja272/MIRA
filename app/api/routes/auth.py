from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from fastapi.security import (
    OAuth2PasswordRequestForm,
)

from app.api.dependencies.auth import (
    CurrentUser,
)
from app.core.config import settings
from app.core.notices import (
    DEVELOPMENT_PRIVACY_NOTICE,
)
from app.core.security import (
    create_access_token,
)
from app.schemas.auth import (
    RegisterRequest,
    RegistrationResponse,
    TokenResponse,
    UserResponse,
)
from app.services.user_service import (
    DuplicateEmailError,
    UserService,
)


router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
)


@router.post(
    "/register",
    response_model=RegistrationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an account",
)
def register(
    request: RegisterRequest,
) -> dict:
    try:
        user = UserService.create_user(
            email=str(request.email),
            password=request.password,
        )

    except DuplicateEmailError as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_409_CONFLICT
            ),
            detail=(
                "An account with this email "
                "already exists."
            ),
        ) from exc

    return {
        "user": user,
        "development_notice": (
            DEVELOPMENT_PRIVACY_NOTICE
        ),
    }


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Log in and receive an access token",
)
def login(
    form_data: Annotated[
        OAuth2PasswordRequestForm,
        Depends(),
    ],
) -> dict:
    """
    Enter the account email in the OAuth2 `username` field.
    """
    user = UserService.authenticate(
        email=form_data.username,
        password=form_data.password,
    )

    if user is None:
        raise HTTPException(
            status_code=(
                status.HTTP_401_UNAUTHORIZED
            ),
            detail=(
                "Invalid email or password."
            ),
            headers={
                "WWW-Authenticate": "Bearer"
            },
        )

    access_token = (
        create_access_token(
            user.user_id
        )
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": (
            settings
            .access_token_expire_minutes
            * 60
        ),
    }


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get the authenticated account",
)
def get_me(
    current_user: CurrentUser,
):
    return current_user
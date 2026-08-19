from fastapi import (
    APIRouter,
    HTTPException,
    Request,
    Response,
    status,
)
from fastapi.security import (
    OAuth2PasswordRequestForm,
)
from fastapi import Depends

from app.api.dependencies.auth import (
    CurrentUser,
)
from app.core.auth_cookies import (
    clear_auth_cookies,
    set_auth_cookies,
)
from app.core.config import settings
from app.core.notices import (
    DEVELOPMENT_PRIVACY_NOTICE,
)
from app.core.security import (
    create_access_token,
    generate_csrf_token,
)
from app.core.security_config import (
    security_settings,
)
from app.schemas.auth import (
    AuthSessionResponse,
    LogoutResponse,
    RegisterRequest,
    RegistrationResponse,
    UserResponse,
)
from app.services.refresh_session_service import (
    RefreshSessionError,
    RefreshSessionService,
)
from app.services.user_service import (
    DuplicateEmailError,
    UserService,
)


router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
)


def _session_response(
    user,
) -> AuthSessionResponse:
    return AuthSessionResponse(
        user=UserResponse.model_validate(
            user
        ),
        expires_in=(
            settings
            .access_token_expire_minutes
            * 60
        ),
        development_notice=(
            DEVELOPMENT_PRIVACY_NOTICE
        ),
    )


@router.post(
    "/register",
    response_model=(
        RegistrationResponse
    ),
    status_code=(
        status.HTTP_201_CREATED
    ),
)
def register(
    request_body: RegisterRequest,
    request: Request,
) -> RegistrationResponse:
    try:
        user = UserService.create_user(
            email=request_body.email,
            password=(
                request_body.password
            ),
        )

    except DuplicateEmailError as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_409_CONFLICT
            ),
            detail=(
                "An account with this "
                "email already exists."
            ),
        ) from exc

    request.state.user_id = (
        user.user_id
    )

    return RegistrationResponse(
        user=UserResponse.model_validate(
            user
        ),
        development_notice=(
            DEVELOPMENT_PRIVACY_NOTICE
        ),
    )


@router.post(
    "/login",
    response_model=(
        AuthSessionResponse
    ),
)
def login(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = (
        Depends()
    ),
) -> AuthSessionResponse:
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
        )

    access_token = (
        create_access_token(
            user.user_id
        )
    )

    refresh_token = (
        RefreshSessionService.create(
            user_id=user.user_id
        )
    )

    csrf_token = (
        generate_csrf_token()
    )

    set_auth_cookies(
        response=response,
        access_token=access_token,
        refresh_token=refresh_token,
        csrf_token=csrf_token,
    )

    request.state.user_id = (
        user.user_id
    )

    return _session_response(
        user
    )


@router.post(
    "/refresh",
    response_model=(
        AuthSessionResponse
    ),
)
def refresh(
    request: Request,
    response: Response,
) -> AuthSessionResponse:
    refresh_token = (
        request.cookies.get(
            security_settings
            .refresh_cookie_name
        )
    )

    if not refresh_token:
        clear_auth_cookies(
            response
        )

        raise HTTPException(
            status_code=(
                status.HTTP_401_UNAUTHORIZED
            ),
            detail=(
                "Refresh session "
                "is not available."
            ),
        )

    try:
        (
            user_id,
            rotated_refresh_token,
        ) = (
            RefreshSessionService
            .rotate(
                refresh_token
            )
        )

    except RefreshSessionError as exc:
        clear_auth_cookies(
            response
        )

        raise HTTPException(
            status_code=(
                status.HTTP_401_UNAUTHORIZED
            ),
            detail=(
                "Refresh session "
                "is invalid or expired."
            ),
        ) from exc

    user = (
        UserService.get_by_user_id(
            user_id
        )
    )

    if (
        user is None
        or not user.is_active
    ):
        clear_auth_cookies(
            response
        )

        raise HTTPException(
            status_code=(
                status.HTTP_401_UNAUTHORIZED
            ),
            detail=(
                "The account is "
                "not available."
            ),
        )

    access_token = (
        create_access_token(
            user.user_id
        )
    )

    csrf_token = (
        generate_csrf_token()
    )

    set_auth_cookies(
        response=response,
        access_token=access_token,
        refresh_token=(
            rotated_refresh_token
        ),
        csrf_token=csrf_token,
    )

    request.state.user_id = (
        user.user_id
    )

    return _session_response(
        user
    )


@router.post(
    "/logout",
    response_model=LogoutResponse,
)
def logout(
    request: Request,
    response: Response,
) -> LogoutResponse:
    refresh_token = (
        request.cookies.get(
            security_settings
            .refresh_cookie_name
        )
    )

    if refresh_token:
        RefreshSessionService.revoke(
            refresh_token
        )

    clear_auth_cookies(
        response
    )

    return LogoutResponse(
        logged_out=True,
        message=(
            "The session was "
            "logged out."
        ),
    )


@router.get(
    "/me",
    response_model=UserResponse,
)
def get_me(
    current_user: CurrentUser,
) -> UserResponse:
    return UserResponse.model_validate(
        current_user
    )
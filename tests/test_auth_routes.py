import unittest
from types import SimpleNamespace
from unittest.mock import patch

from datetime import (
    datetime,
    timezone,
)

from fastapi import HTTPException
from starlette.requests import Request
from starlette.responses import Response

from app.api.routes.auth import (
    login,
    register,
)
from app.schemas.auth import (
    RegisterRequest,
)
from app.services.user_service import (
    DuplicateEmailError,
)


def build_request(
    path: str = "/auth/test",
    method: str = "POST",
) -> Request:
    scope = {
        "type": "http",
        "asgi": {
            "version": "3.0",
        },
        "http_version": "1.1",
        "method": method,
        "scheme": "http",
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
        "headers": [],
        "client": (
            "127.0.0.1",
            12345,
        ),
        "server": (
            "127.0.0.1",
            8001,
        ),
    }

    return Request(scope)


class AuthRouteTests(
    unittest.TestCase
):
    @patch(
        "app.api.routes.auth."
        "UserService.create_user"
    )
    def test_register_returns_user_and_notice(
        self,
        mock_create_user,
    ):
        user = SimpleNamespace(
            user_id="user-1",
            email="person@example.com",
            is_active=True,
            created_at=datetime.now(
                timezone.utc
            ),
        )

        mock_create_user.return_value = (
            user
        )

        request = build_request(
            path="/auth/register",
        )

        result = register(
            RegisterRequest(
                email="PERSON@example.com",
                password=(
                    "DevelopmentPassword123!"
                ),
            ),
            request,
        )

        self.assertEqual(
            result.user.user_id,
            "user-1",
        )

        self.assertEqual(
            result.user.email,
            "person@example.com",
        )

        self.assertIn(
            "Do not upload real medical",
            result.development_notice,
        )

        self.assertEqual(
            request.state.user_id,
            "user-1",
        )

        mock_create_user.assert_called_once_with(
            email="person@example.com",
            password=(
                "DevelopmentPassword123!"
            ),
        )

    @patch(
        "app.api.routes.auth."
        "UserService.create_user"
    )
    def test_register_rejects_duplicate_email(
        self,
        mock_create_user,
    ):
        mock_create_user.side_effect = (
            DuplicateEmailError()
        )

        request = build_request(
            path="/auth/register",
        )

        with self.assertRaises(
            HTTPException
        ) as context:
            register(
                RegisterRequest(
                    email=(
                        "person@example.com"
                    ),
                    password=(
                        "DevelopmentPassword123!"
                    ),
                ),
                request,
            )

        self.assertEqual(
            context.exception.status_code,
            409,
        )

    @patch(
        "app.api.routes.auth."
        "set_auth_cookies"
    )
    @patch(
        "app.api.routes.auth."
        "generate_csrf_token",
        return_value="csrf-token",
    )
    @patch(
        "app.api.routes.auth."
        "RefreshSessionService.create",
        return_value="refresh-token",
    )
    @patch(
        "app.api.routes.auth."
        "create_access_token",
        return_value="access-token",
    )
    @patch(
        "app.api.routes.auth."
        "UserService.authenticate"
    )
    def test_login_sets_cookie_session(
        self,
        mock_authenticate,
        mock_create_access_token,
        mock_create_refresh_token,
        mock_generate_csrf_token,
        mock_set_auth_cookies,
    ):
        user = SimpleNamespace(
            user_id="user-1",
            email="person@example.com",
            is_active=True,
            created_at=datetime.now(
                timezone.utc
            ),
        )

        mock_authenticate.return_value = (
            user
        )

        form = SimpleNamespace(
            username="person@example.com",
            password=(
                "DevelopmentPassword123!"
            ),
        )

        request = build_request(
            path="/auth/login",
        )

        response = Response()

        result = login(
            request,
            response,
            form,
        )

        self.assertEqual(
            result.user.user_id,
            "user-1",
        )

        self.assertEqual(
            result.user.email,
            "person@example.com",
        )

        self.assertGreater(
            result.expires_in,
            0,
        )

        self.assertFalse(
            hasattr(
                result,
                "access_token",
            )
        )

        self.assertEqual(
            request.state.user_id,
            "user-1",
        )

        mock_authenticate.assert_called_once_with(
            email="person@example.com",
            password=(
                "DevelopmentPassword123!"
            ),
        )

        mock_create_access_token.assert_called_once_with(
            "user-1"
        )

        mock_create_refresh_token.assert_called_once_with(
            user_id="user-1"
        )

        mock_generate_csrf_token.assert_called_once_with()

        mock_set_auth_cookies.assert_called_once_with(
            response=response,
            access_token="access-token",
            refresh_token="refresh-token",
            csrf_token="csrf-token",
        )


if __name__ == "__main__":
    unittest.main()
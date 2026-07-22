import unittest
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import HTTPException

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
            created_at=None,
        )

        mock_create_user.return_value = (
            user
        )

        result = register(
            RegisterRequest(
                email="PERSON@example.com",
                password=(
                    "DevelopmentPassword123!"
                ),
            )
        )

        self.assertEqual(
            result["user"],
            user,
        )

        self.assertIn(
            "Do not upload real medical",
            result[
                "development_notice"
            ],
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
                )
            )

        self.assertEqual(
            context.exception.status_code,
            409,
        )

    @patch(
        "app.api.routes.auth."
        "create_access_token",
        return_value="signed-token",
    )
    @patch(
        "app.api.routes.auth."
        "UserService.authenticate"
    )
    def test_login_returns_token(
        self,
        mock_authenticate,
        mock_create_access_token,
    ):
        mock_authenticate.return_value = (
            SimpleNamespace(
                user_id="user-1",
                is_active=True,
            )
        )

        form = SimpleNamespace(
            username="person@example.com",
            password=(
                "DevelopmentPassword123!"
            ),
        )

        result = login(
            form
        )

        self.assertEqual(
            result["access_token"],
            "signed-token",
        )

        self.assertEqual(
            result["token_type"],
            "bearer",
        )

        mock_create_access_token.assert_called_once_with(
            "user-1"
        )


if __name__ == "__main__":
    unittest.main()
import unittest
from uuid import uuid4

from app.core.csrf import (
    validate_csrf_tokens,
)
from app.core.security import (
    TokenValidationError,
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
    generate_csrf_token,
    hash_token,
)


class Batch7SecurityTests(
    unittest.TestCase
):
    def test_access_token_round_trip(
        self,
    ):
        user_id = str(
            uuid4()
        )

        token = (
            create_access_token(
                user_id
            )
        )

        self.assertEqual(
            decode_access_token(
                token
            ),
            user_id,
        )

    def test_refresh_token_round_trip(
        self,
    ):
        user_id = str(
            uuid4()
        )

        session_id = str(
            uuid4()
        )

        token = (
            create_refresh_token(
                user_id=user_id,
                session_id=(
                    session_id
                ),
            )
        )

        decoded_user_id, (
            decoded_session_id
        ) = decode_refresh_token(
            token
        )

        self.assertEqual(
            decoded_user_id,
            user_id,
        )

        self.assertEqual(
            decoded_session_id,
            session_id,
        )

    def test_access_token_cannot_be_used_as_refresh_token(
        self,
    ):
        token = (
            create_access_token(
                str(uuid4())
            )
        )

        with self.assertRaises(
            TokenValidationError
        ):
            decode_refresh_token(
                token
            )

    def test_refresh_token_cannot_be_used_as_access_token(
        self,
    ):
        token = (
            create_refresh_token(
                user_id=str(
                    uuid4()
                ),
                session_id=str(
                    uuid4()
                ),
            )
        )

        with self.assertRaises(
            TokenValidationError
        ):
            decode_access_token(
                token
            )

    def test_csrf_match_is_required(
        self,
    ):
        token = (
            generate_csrf_token()
        )

        self.assertTrue(
            validate_csrf_tokens(
                cookie_token=token,
                header_token=token,
            )
        )

        self.assertFalse(
            validate_csrf_tokens(
                cookie_token=token,
                header_token=(
                    "different"
                ),
            )
        )

        self.assertFalse(
            validate_csrf_tokens(
                cookie_token=token,
                header_token=None,
            )
        )

    def test_csrf_tokens_are_random(
        self,
    ):
        first = (
            generate_csrf_token()
        )

        second = (
            generate_csrf_token()
        )

        self.assertNotEqual(
            first,
            second,
        )

    def test_refresh_token_hash_is_deterministic(
        self,
    ):
        token = "synthetic-token"

        self.assertEqual(
            hash_token(token),
            hash_token(token),
        )

        self.assertNotEqual(
            hash_token(token),
            hash_token(
                "different-token"
            ),
        )


if __name__ == "__main__":
    unittest.main()
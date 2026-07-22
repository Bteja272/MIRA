import unittest

from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


class SecurityTests(
    unittest.TestCase
):
    def test_password_hashing_and_verification(
        self,
    ):
        password = (
            "DevelopmentPassword123!"
        )

        stored_hash = hash_password(
            password
        )

        self.assertNotEqual(
            password,
            stored_hash,
        )

        self.assertTrue(
            verify_password(
                plain_password=password,
                stored_password_hash=(
                    stored_hash
                ),
            )
        )

        self.assertFalse(
            verify_password(
                plain_password=(
                    "WrongPassword123!"
                ),
                stored_password_hash=(
                    stored_hash
                ),
            )
        )

    def test_access_token_round_trip(
        self,
    ):
        user_id = (
            "test-user-id"
        )

        token = create_access_token(
            user_id
        )

        decoded_user_id = (
            decode_access_token(
                token
            )
        )

        self.assertEqual(
            decoded_user_id,
            user_id,
        )


if __name__ == "__main__":
    unittest.main()
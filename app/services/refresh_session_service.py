from __future__ import annotations

import hmac
from datetime import (
    datetime,
    timedelta,
    timezone,
)
from uuid import uuid4

from sqlalchemy import text

from app.core.security import (
    TokenValidationError,
    create_refresh_token,
    decode_refresh_token,
    hash_token,
)
from app.core.security_config import (
    security_settings,
)
from app.db.session import (
    SessionLocal,
)


class RefreshSessionError(
    RuntimeError
):
    pass


class RefreshSessionService:
    @staticmethod
    def create(
        *,
        user_id: str,
    ) -> str:
        session_id = str(
            uuid4()
        )

        refresh_token = (
            create_refresh_token(
                user_id=user_id,
                session_id=session_id,
            )
        )

        now = datetime.now(
            timezone.utc
        )

        expires_at = (
            now
            + timedelta(
                days=(
                    security_settings
                    .refresh_token_expire_days
                )
            )
        )

        db = SessionLocal()

        try:
            db.execute(
                text(
                    """
                    INSERT INTO refresh_sessions (
                        session_id,
                        user_id,
                        token_hash,
                        created_at,
                        expires_at,
                        last_used_at,
                        revoked_at,
                        replaced_by_session_id
                    )
                    VALUES (
                        :session_id,
                        :user_id,
                        :token_hash,
                        :created_at,
                        :expires_at,
                        NULL,
                        NULL,
                        NULL
                    )
                    """
                ),
                {
                    "session_id": (
                        session_id
                    ),
                    "user_id": user_id,
                    "token_hash": (
                        hash_token(
                            refresh_token
                        )
                    ),
                    "created_at": now,
                    "expires_at": (
                        expires_at
                    ),
                },
            )

            db.commit()

            return refresh_token

        except Exception:
            db.rollback()
            raise

        finally:
            db.close()

    @staticmethod
    def rotate(
        refresh_token: str,
    ) -> tuple[str, str]:
        try:
            (
                user_id,
                session_id,
            ) = decode_refresh_token(
                refresh_token
            )

        except TokenValidationError as exc:
            raise RefreshSessionError(
                "Invalid refresh session."
            ) from exc

        presented_hash = hash_token(
            refresh_token
        )

        now = datetime.now(
            timezone.utc
        )

        new_session_id = str(
            uuid4()
        )

        new_refresh_token = (
            create_refresh_token(
                user_id=user_id,
                session_id=(
                    new_session_id
                ),
            )
        )

        new_expiry = (
            now
            + timedelta(
                days=(
                    security_settings
                    .refresh_token_expire_days
                )
            )
        )

        db = SessionLocal()

        try:
            row = (
                db.execute(
                    text(
                        """
                        SELECT
                            session_id,
                            user_id,
                            token_hash,
                            expires_at,
                            revoked_at
                        FROM refresh_sessions
                        WHERE session_id = :session_id
                        FOR UPDATE
                        """
                    ),
                    {
                        "session_id": (
                            session_id
                        ),
                    },
                )
                .mappings()
                .one_or_none()
            )

            if row is None:
                raise RefreshSessionError(
                    "Refresh session "
                    "was not found."
                )

            if (
                row["user_id"]
                != user_id
            ):
                raise RefreshSessionError(
                    "Refresh session owner "
                    "does not match."
                )

            if (
                row["revoked_at"]
                is not None
            ):
                raise RefreshSessionError(
                    "Refresh session has "
                    "already been revoked."
                )

            expires_at = row[
                "expires_at"
            ]

            if (
                expires_at.tzinfo
                is None
            ):
                expires_at = (
                    expires_at.replace(
                        tzinfo=timezone.utc
                    )
                )

            if expires_at <= now:
                db.execute(
                    text(
                        """
                        UPDATE refresh_sessions
                        SET revoked_at = :now
                        WHERE session_id = :session_id
                        """
                    ),
                    {
                        "now": now,
                        "session_id": (
                            session_id
                        ),
                    },
                )

                db.commit()

                raise RefreshSessionError(
                    "Refresh session "
                    "has expired."
                )

            stored_hash = str(
                row["token_hash"]
            )

            if not hmac.compare_digest(
                stored_hash,
                presented_hash,
            ):
                raise RefreshSessionError(
                    "Refresh token does "
                    "not match session."
                )

            db.execute(
                text(
                    """
                    UPDATE refresh_sessions
                    SET
                        last_used_at = :now,
                        revoked_at = :now,
                        replaced_by_session_id =
                            :replacement
                    WHERE session_id =
                        :session_id
                    """
                ),
                {
                    "now": now,
                    "replacement": (
                        new_session_id
                    ),
                    "session_id": (
                        session_id
                    ),
                },
            )

            db.execute(
                text(
                    """
                    INSERT INTO refresh_sessions (
                        session_id,
                        user_id,
                        token_hash,
                        created_at,
                        expires_at,
                        last_used_at,
                        revoked_at,
                        replaced_by_session_id
                    )
                    VALUES (
                        :session_id,
                        :user_id,
                        :token_hash,
                        :created_at,
                        :expires_at,
                        NULL,
                        NULL,
                        NULL
                    )
                    """
                ),
                {
                    "session_id": (
                        new_session_id
                    ),
                    "user_id": user_id,
                    "token_hash": (
                        hash_token(
                            new_refresh_token
                        )
                    ),
                    "created_at": now,
                    "expires_at": (
                        new_expiry
                    ),
                },
            )

            db.commit()

            return (
                user_id,
                new_refresh_token,
            )

        except RefreshSessionError:
            db.rollback()
            raise

        except Exception as exc:
            db.rollback()

            raise RefreshSessionError(
                "Refresh session rotation "
                "failed."
            ) from exc

        finally:
            db.close()

    @staticmethod
    def revoke(
        refresh_token: str,
    ) -> bool:
        try:
            (
                _,
                session_id,
            ) = decode_refresh_token(
                refresh_token
            )

        except TokenValidationError:
            return False

        now = datetime.now(
            timezone.utc
        )

        db = SessionLocal()

        try:
            result = db.execute(
                text(
                    """
                    UPDATE refresh_sessions
                    SET revoked_at = :now
                    WHERE
                        session_id = :session_id
                        AND revoked_at IS NULL
                    """
                ),
                {
                    "now": now,
                    "session_id": (
                        session_id
                    ),
                },
            )

            db.commit()

            return (
                result.rowcount > 0
            )

        except Exception:
            db.rollback()
            raise

        finally:
            db.close()
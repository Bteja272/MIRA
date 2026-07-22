from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.security import (
    hash_password,
    verify_password,
)
from app.db.models import User
from app.db.session import SessionLocal


class DuplicateEmailError(Exception):
    pass


class UserService:
    @staticmethod
    def normalize_email(
        email: str,
    ) -> str:
        return email.strip().lower()

    @classmethod
    def get_by_email(
        cls,
        email: str,
    ) -> User | None:
        normalized_email = (
            cls.normalize_email(email)
        )

        statement = (
            select(User)
            .where(
                User.email
                == normalized_email
            )
            .limit(1)
        )

        db = SessionLocal()

        try:
            return db.scalar(
                statement
            )

        finally:
            db.close()

    @staticmethod
    def get_by_user_id(
        user_id: str,
    ) -> User | None:
        statement = (
            select(User)
            .where(
                User.user_id
                == user_id
            )
            .limit(1)
        )

        db = SessionLocal()

        try:
            return db.scalar(
                statement
            )

        finally:
            db.close()

    @classmethod
    def create_user(
        cls,
        email: str,
        password: str,
    ) -> User:
        normalized_email = (
            cls.normalize_email(email)
        )

        db = SessionLocal()

        try:
            user = User(
                user_id=str(uuid4()),
                email=normalized_email,
                password_hash=(
                    hash_password(password)
                ),
                is_active=True,
            )

            db.add(user)
            db.commit()
            db.refresh(user)

            return user

        except IntegrityError as exc:
            db.rollback()

            raise DuplicateEmailError(
                "Unable to create account."
            ) from exc

        except Exception:
            db.rollback()
            raise

        finally:
            db.close()

    @classmethod
    def authenticate(
        cls,
        email: str,
        password: str,
    ) -> User | None:
        user = cls.get_by_email(
            email
        )

        if user is None:
            return None

        if not verify_password(
            plain_password=password,
            stored_password_hash=(
                user.password_hash
            ),
        ):
            return None

        if not user.is_active:
            return None

        return user
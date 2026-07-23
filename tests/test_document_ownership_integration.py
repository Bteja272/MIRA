import os
import unittest
from uuid import uuid4

from sqlalchemy import delete
from sqlalchemy.exc import IntegrityError

from app.db.models import (
    Document,
    User,
)
from app.db.session import SessionLocal
from app.services.document_service import (
    DocumentService,
)


RUN_DB_TESTS = (
    os.getenv(
        "RUN_DB_INTEGRATION_TESTS"
    )
    == "1"
)


@unittest.skipUnless(
    RUN_DB_TESTS,
    (
        "Set RUN_DB_INTEGRATION_TESTS=1 "
        "to run PostgreSQL integration tests."
    ),
)
class DocumentOwnershipIntegrationTests(
    unittest.TestCase
):
    def setUp(self) -> None:
        unique_suffix = uuid4().hex

        self.user_one_id = str(
            uuid4()
        )

        self.user_two_id = str(
            uuid4()
        )

        self.user_one_email = (
            f"ownership-user-one-"
            f"{unique_suffix}@example.com"
        )

        self.user_two_email = (
            f"ownership-user-two-"
            f"{unique_suffix}@example.com"
        )

        self.document_one_id = str(
            uuid4()
        )

        self.document_two_id = str(
            uuid4()
        )

        self.shared_file_hash = (
            uuid4().hex
            + uuid4().hex
        )

        db = SessionLocal()

        try:
            user_one = User(
                user_id=self.user_one_id,
                email=self.user_one_email,
                password_hash=(
                    "integration-test-password-hash"
                ),
                is_active=True,
            )

            user_two = User(
                user_id=self.user_two_id,
                email=self.user_two_email,
                password_hash=(
                    "integration-test-password-hash"
                ),
                is_active=True,
            )

            document_one = Document(
                document_id=(
                    self.document_one_id
                ),
                user_id=self.user_one_id,
                source=(
                    "user_one_report.txt"
                ),
                original_filename=(
                    "user_one_report.txt"
                ),
                stored_filename=(
                    f"{self.document_one_id}.txt"
                ),
                document_type=(
                    "lab_report"
                ),
                file_hash=(
                    self.shared_file_hash
                ),
                file_size_bytes=128,
            )

            document_two = Document(
                document_id=(
                    self.document_two_id
                ),
                user_id=self.user_two_id,
                source=(
                    "user_two_report.txt"
                ),
                original_filename=(
                    "user_two_report.txt"
                ),
                stored_filename=(
                    f"{self.document_two_id}.txt"
                ),
                document_type=(
                    "lab_report"
                ),
                file_hash=(
                    self.shared_file_hash
                ),
                file_size_bytes=128,
            )

            db.add_all(
                [
                    user_one,
                    user_two,
                ]
            )

            db.flush()

            db.add_all(
                [
                    document_one,
                    document_two,
                ]
            )

            db.commit()

        except Exception:
            db.rollback()
            raise

        finally:
            db.close()

    def tearDown(self) -> None:
        db = SessionLocal()

        try:
            db.execute(
                delete(Document).where(
                    Document.user_id.in_(
                        [
                            self.user_one_id,
                            self.user_two_id,
                        ]
                    )
                )
            )

            db.execute(
                delete(User).where(
                    User.user_id.in_(
                        [
                            self.user_one_id,
                            self.user_two_id,
                        ]
                    )
                )
            )

            db.commit()

        except Exception:
            db.rollback()
            raise

        finally:
            db.close()

    def test_user_can_read_owned_document(
        self,
    ) -> None:
        document = (
            DocumentService.get_document(
                document_id=(
                    self.document_one_id
                ),
                user_id=(
                    self.user_one_id
                ),
            )
        )

        self.assertIsNotNone(
            document
        )

        self.assertEqual(
            document["document_id"],
            self.document_one_id,
        )

    def test_user_cannot_read_another_users_document(
        self,
    ) -> None:
        document = (
            DocumentService.get_document(
                document_id=(
                    self.document_one_id
                ),
                user_id=(
                    self.user_two_id
                ),
            )
        )

        self.assertIsNone(
            document
        )

    def test_existing_ids_are_scoped_to_owner(
        self,
    ) -> None:
        existing_ids = (
            DocumentService
            .get_existing_document_ids(
                document_ids=[
                    self.document_one_id,
                    self.document_two_id,
                ],
                user_id=(
                    self.user_one_id
                ),
            )
        )

        self.assertEqual(
            existing_ids,
            [
                self.document_one_id
            ],
        )

    def test_document_list_is_scoped_to_owner(
        self,
    ) -> None:
        user_one_documents = (
            DocumentService.list_documents(
                user_id=(
                    self.user_one_id
                )
            )
        )

        returned_ids = {
            document["document_id"]
            for document
            in user_one_documents
        }

        self.assertIn(
            self.document_one_id,
            returned_ids,
        )

        self.assertNotIn(
            self.document_two_id,
            returned_ids,
        )

    def test_duplicate_detection_is_scoped_to_owner(
        self,
    ) -> None:
        user_one_duplicate = (
            DocumentService
            .find_duplicate_by_hash(
                file_hash=(
                    self.shared_file_hash
                ),
                user_id=(
                    self.user_one_id
                ),
            )
        )

        user_two_duplicate = (
            DocumentService
            .find_duplicate_by_hash(
                file_hash=(
                    self.shared_file_hash
                ),
                user_id=(
                    self.user_two_id
                ),
            )
        )

        self.assertEqual(
            user_one_duplicate[
                "document_id"
            ],
            self.document_one_id,
        )

        self.assertEqual(
            user_two_duplicate[
                "document_id"
            ],
            self.document_two_id,
        )

    def test_database_rejects_ownerless_document(
        self,
    ) -> None:
        db = SessionLocal()

        try:
            ownerless_document = Document(
                document_id=str(
                    uuid4()
                ),
                user_id=None,
                source=(
                    "ownerless.txt"
                ),
                original_filename=(
                    "ownerless.txt"
                ),
                stored_filename=(
                    f"{uuid4()}.txt"
                ),
                document_type="unknown",
                file_hash=(
                    uuid4().hex
                    + uuid4().hex
                ),
                file_size_bytes=32,
            )

            db.add(
                ownerless_document
            )

            with self.assertRaises(
                IntegrityError
            ):
                db.commit()

        finally:
            db.rollback()
            db.close()

    def test_database_rejects_unknown_owner(
        self,
    ) -> None:
        db = SessionLocal()

        try:
            invalid_document = Document(
                document_id=str(
                    uuid4()
                ),
                user_id=(
                    "nonexistent-user-id"
                ),
                source=(
                    "invalid-owner.txt"
                ),
                original_filename=(
                    "invalid-owner.txt"
                ),
                stored_filename=(
                    f"{uuid4()}.txt"
                ),
                document_type="unknown",
                file_hash=(
                    uuid4().hex
                    + uuid4().hex
                ),
                file_size_bytes=32,
            )

            db.add(
                invalid_document
            )

            with self.assertRaises(
                IntegrityError
            ):
                db.commit()

        finally:
            db.rollback()
            db.close()


if __name__ == "__main__":
    unittest.main()
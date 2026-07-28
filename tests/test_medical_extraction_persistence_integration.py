import os
import unittest
from uuid import uuid4

from sqlalchemy import (
    delete,
    func,
    select,
)

from app.db.extraction_models import (
    DocumentExtraction,
)
from app.db.models import (
    Document,
    User,
)
from app.db.session import SessionLocal
from app.schemas.medical_extraction import (
    ExtractionMethod,
    ExtractionStatus,
    MedicalDocumentExtraction,
    MedicalDocumentType,
)
from app.services.medical_extraction_persistence_service import (
    MedicalExtractionPersistenceNotFoundError,
    MedicalExtractionPersistenceService,
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
class MedicalExtractionPersistenceIntegrationTests(
    unittest.TestCase
):
    def setUp(self) -> None:
        suffix = uuid4().hex

        self.user_one_id = str(
            uuid4()
        )

        self.user_two_id = str(
            uuid4()
        )

        self.document_one_id = str(
            uuid4()
        )

        self.document_two_id = str(
            uuid4()
        )

        db = SessionLocal()

        try:
            user_one = User(
                user_id=self.user_one_id,
                email=(
                    f"extract-one-{suffix}"
                    "@example.com"
                ),
                password_hash=(
                    "integration-test-hash"
                ),
                is_active=True,
            )

            user_two = User(
                user_id=self.user_two_id,
                email=(
                    f"extract-two-{suffix}"
                    "@example.com"
                ),
                password_hash=(
                    "integration-test-hash"
                ),
                is_active=True,
            )

            db.add_all(
                [
                    user_one,
                    user_two,
                ]
            )

            db.flush()

            document_one = Document(
                document_id=(
                    self.document_one_id
                ),
                user_id=self.user_one_id,
                source="report-one.txt",
                original_filename=(
                    "report-one.txt"
                ),
                stored_filename=(
                    f"{self.document_one_id}.txt"
                ),
                document_type=(
                    "lab_report"
                ),
                file_hash=(
                    uuid4().hex
                    + uuid4().hex
                ),
                file_size_bytes=128,
            )

            document_two = Document(
                document_id=(
                    self.document_two_id
                ),
                user_id=self.user_two_id,
                source="report-two.txt",
                original_filename=(
                    "report-two.txt"
                ),
                stored_filename=(
                    f"{self.document_two_id}.txt"
                ),
                document_type=(
                    "lab_report"
                ),
                file_hash=(
                    uuid4().hex
                    + uuid4().hex
                ),
                file_size_bytes=128,
            )

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
                delete(
                    DocumentExtraction
                ).where(
                    DocumentExtraction.user_id.in_(
                        [
                            self.user_one_id,
                            self.user_two_id,
                        ]
                    )
                )
            )

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

    def _build_extraction(
        self,
        confidence: float = 0.90,
    ) -> MedicalDocumentExtraction:
        return MedicalDocumentExtraction(
            document_id=(
                self.document_one_id
            ),
            document_type=(
                MedicalDocumentType
                .LAB_REPORT
            ),
            status=(
                ExtractionStatus.COMPLETED
            ),
            extraction_confidence=(
                confidence
            ),
        )

    def test_save_and_get_extraction(
        self,
    ) -> None:
        saved = (
            MedicalExtractionPersistenceService
            .save(
                extraction=(
                    self._build_extraction()
                ),
                user_id=self.user_one_id,
                model_name=(
                    "integration-test-model"
                ),
                extraction_method=(
                    ExtractionMethod.HYBRID
                ),
            )
        )

        loaded = (
            MedicalExtractionPersistenceService
            .get(
                document_id=(
                    self.document_one_id
                ),
                user_id=self.user_one_id,
            )
        )

        self.assertIsNotNone(
            loaded
        )

        self.assertEqual(
            loaded.extraction_id,
            saved.extraction_id,
        )

        self.assertEqual(
            loaded.document_id,
            self.document_one_id,
        )

    def test_replacing_extraction_preserves_id(
        self,
    ) -> None:
        first = (
            MedicalExtractionPersistenceService
            .save(
                extraction=(
                    self._build_extraction(
                        confidence=0.70
                    )
                ),
                user_id=self.user_one_id,
                model_name=(
                    "integration-test-model"
                ),
            )
        )

        second = (
            MedicalExtractionPersistenceService
            .save(
                extraction=(
                    self._build_extraction(
                        confidence=0.98
                    )
                ),
                user_id=self.user_one_id,
                model_name=(
                    "integration-test-model"
                ),
            )
        )

        self.assertEqual(
            first.extraction_id,
            second.extraction_id,
        )

        self.assertEqual(
            second.extraction
            .extraction_confidence,
            0.98,
        )

        db = SessionLocal()

        try:
            count = db.scalar(
                select(
                    func.count(
                        DocumentExtraction.id
                    )
                ).where(
                    DocumentExtraction.document_id
                    == self.document_one_id
                )
            )

        finally:
            db.close()

        self.assertEqual(
            count,
            1,
        )

    def test_other_user_cannot_read_extraction(
        self,
    ) -> None:
        (
            MedicalExtractionPersistenceService
            .save(
                extraction=(
                    self._build_extraction()
                ),
                user_id=self.user_one_id,
                model_name=(
                    "integration-test-model"
                ),
            )
        )

        loaded = (
            MedicalExtractionPersistenceService
            .get(
                document_id=(
                    self.document_one_id
                ),
                user_id=self.user_two_id,
            )
        )

        self.assertIsNone(
            loaded
        )

    def test_other_user_cannot_save_extraction(
        self,
    ) -> None:
        with self.assertRaises(
            MedicalExtractionPersistenceNotFoundError
        ):
            (
                MedicalExtractionPersistenceService
                .save(
                    extraction=(
                        self._build_extraction()
                    ),
                    user_id=(
                        self.user_two_id
                    ),
                    model_name=(
                        "integration-test-model"
                    ),
                )
            )

    def test_delete_extraction(
        self,
    ) -> None:
        (
            MedicalExtractionPersistenceService
            .save(
                extraction=(
                    self._build_extraction()
                ),
                user_id=self.user_one_id,
                model_name=(
                    "integration-test-model"
                ),
            )
        )

        deleted = (
            MedicalExtractionPersistenceService
            .delete(
                document_id=(
                    self.document_one_id
                ),
                user_id=self.user_one_id,
            )
        )

        self.assertTrue(
            deleted
        )

        loaded = (
            MedicalExtractionPersistenceService
            .get(
                document_id=(
                    self.document_one_id
                ),
                user_id=self.user_one_id,
            )
        )

        self.assertIsNone(
            loaded
        )

    def test_document_delete_cascades_extraction(
        self,
    ) -> None:
        (
            MedicalExtractionPersistenceService
            .save(
                extraction=(
                    self._build_extraction()
                ),
                user_id=self.user_one_id,
                model_name=(
                    "integration-test-model"
                ),
            )
        )

        db = SessionLocal()

        try:
            db.execute(
                delete(Document).where(
                    Document.document_id
                    == self.document_one_id
                )
            )

            db.commit()

            extraction_count = db.scalar(
                select(
                    func.count(
                        DocumentExtraction.id
                    )
                ).where(
                    DocumentExtraction.document_id
                    == self.document_one_id
                )
            )

        except Exception:
            db.rollback()
            raise

        finally:
            db.close()

        self.assertEqual(
            extraction_count,
            0,
        )


if __name__ == "__main__":
    unittest.main()
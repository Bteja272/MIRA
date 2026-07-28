import unittest
from datetime import (
    datetime,
    timezone,
)
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import HTTPException

from app.api.routes.extractions import (
    delete_document_extraction,
    generate_document_extraction,
    get_document_extraction,
)
from app.schemas.extraction_api import (
    ExtractionGenerateRequest,
)
from app.schemas.extraction_persistence import (
    PersistedMedicalExtraction,
)
from app.schemas.medical_extraction import (
    ExtractionMethod,
    ExtractionStatus,
    MedicalDocumentExtraction,
    MedicalDocumentType,
)
from app.services.medical_extraction_service import (
    MedicalExtractionContentTooLargeError,
    MedicalExtractionNotFoundError,
    MedicalExtractionValidationError,
)


class ExtractionRouteTests(
    unittest.TestCase
):
    def setUp(self) -> None:
        self.current_user = (
            SimpleNamespace(
                user_id="user-123"
            )
        )

        self.document_id = (
            "document-123"
        )

    def _extraction(
        self,
    ) -> MedicalDocumentExtraction:
        return (
            MedicalDocumentExtraction(
                document_id=(
                    self.document_id
                ),
                document_type=(
                    MedicalDocumentType
                    .LAB_REPORT
                ),
                status=(
                    ExtractionStatus
                    .COMPLETED
                ),
                extraction_confidence=0.95,
            )
        )

    def _persisted(
        self,
    ) -> PersistedMedicalExtraction:
        extraction = (
            self._extraction()
            .model_copy(
                update={
                    "extraction_id": (
                        "extraction-123"
                    )
                }
            )
        )

        timestamp = datetime.now(
            timezone.utc
        )

        return PersistedMedicalExtraction(
            extraction_id=(
                "extraction-123"
            ),
            document_id=(
                self.document_id
            ),
            schema_version="1.0",
            status=(
                ExtractionStatus.COMPLETED
            ),
            extraction_method=(
                ExtractionMethod.HYBRID
            ),
            model_name=(
                "integration-test-model"
            ),
            extraction=extraction,
            created_at=timestamp,
            updated_at=timestamp,
        )

    @patch(
        "app.api.routes.extractions."
        "MedicalExtractionService.extract"
    )
    @patch(
        "app.api.routes.extractions."
        "MedicalExtractionPersistenceService.get"
    )
    def test_existing_extraction_is_cached(
        self,
        mock_get,
        mock_extract,
    ) -> None:
        mock_get.return_value = (
            self._persisted()
        )

        result = (
            generate_document_extraction(
                document_id=(
                    self.document_id
                ),
                request=(
                    ExtractionGenerateRequest()
                ),
                current_user=(
                    self.current_user
                ),
            )
        )

        self.assertTrue(
            result.cached
        )

        self.assertFalse(
            result.replaced
        )

        mock_get.assert_called_once_with(
            document_id=(
                self.document_id
            ),
            user_id="user-123",
        )

        mock_extract.assert_not_called()

    @patch(
        "app.api.routes.extractions."
        "MedicalExtractionPersistenceService.save"
    )
    @patch(
        "app.api.routes.extractions."
        "MedicalExtractionService.extract"
    )
    @patch(
        "app.api.routes.extractions."
        "MedicalExtractionPersistenceService.get"
    )
    def test_new_extraction_is_generated_and_saved(
        self,
        mock_get,
        mock_extract,
        mock_save,
    ) -> None:
        extraction = self._extraction()
        persisted = self._persisted()

        mock_get.return_value = None
        mock_extract.return_value = (
            extraction
        )
        mock_save.return_value = (
            persisted
        )

        result = (
            generate_document_extraction(
                document_id=(
                    self.document_id
                ),
                request=(
                    ExtractionGenerateRequest()
                ),
                current_user=(
                    self.current_user
                ),
            )
        )

        self.assertFalse(
            result.cached
        )

        self.assertFalse(
            result.replaced
        )

        mock_extract.assert_called_once_with(
            document_id=(
                self.document_id
            ),
            user_id="user-123",
        )

        mock_save.assert_called_once_with(
            extraction=extraction,
            user_id="user-123",
        )

    @patch(
        "app.api.routes.extractions."
        "MedicalExtractionPersistenceService.save"
    )
    @patch(
        "app.api.routes.extractions."
        "MedicalExtractionService.extract"
    )
    @patch(
        "app.api.routes.extractions."
        "MedicalExtractionPersistenceService.get"
    )
    def test_replace_existing_reruns_extraction(
        self,
        mock_get,
        mock_extract,
        mock_save,
    ) -> None:
        existing = self._persisted()
        extraction = self._extraction()

        mock_get.return_value = existing
        mock_extract.return_value = (
            extraction
        )
        mock_save.return_value = existing

        result = (
            generate_document_extraction(
                document_id=(
                    self.document_id
                ),
                request=(
                    ExtractionGenerateRequest(
                        replace_existing=True
                    )
                ),
                current_user=(
                    self.current_user
                ),
            )
        )

        self.assertFalse(
            result.cached
        )

        self.assertTrue(
            result.replaced
        )

        mock_extract.assert_called_once()

        mock_save.assert_called_once_with(
            extraction=extraction,
            user_id="user-123",
        )

    @patch(
        "app.api.routes.extractions."
        "MedicalExtractionPersistenceService.get",
        return_value=None,
    )
    @patch(
        "app.api.routes.extractions."
        "MedicalExtractionService.extract",
        side_effect=(
            MedicalExtractionNotFoundError(
                "Document not found."
            )
        ),
    )
    def test_unowned_document_returns_404(
        self,
        mock_extract,
        mock_get,
    ) -> None:
        with self.assertRaises(
            HTTPException
        ) as context:
            generate_document_extraction(
                document_id=(
                    "another-users-document"
                ),
                request=(
                    ExtractionGenerateRequest()
                ),
                current_user=(
                    self.current_user
                ),
            )

        self.assertEqual(
            context.exception.status_code,
            404,
        )

    @patch(
        "app.api.routes.extractions."
        "MedicalExtractionPersistenceService.get",
        return_value=None,
    )
    @patch(
        "app.api.routes.extractions."
        "MedicalExtractionService.extract",
        side_effect=(
            MedicalExtractionContentTooLargeError(
                "Too large."
            )
        ),
    )
    def test_large_document_returns_413(
        self,
        mock_extract,
        mock_get,
    ) -> None:
        with self.assertRaises(
            HTTPException
        ) as context:
            generate_document_extraction(
                document_id=(
                    self.document_id
                ),
                request=(
                    ExtractionGenerateRequest()
                ),
                current_user=(
                    self.current_user
                ),
            )

        self.assertEqual(
            context.exception.status_code,
            413,
        )

    @patch(
        "app.api.routes.extractions."
        "MedicalExtractionPersistenceService.get",
        return_value=None,
    )
    @patch(
        "app.api.routes.extractions."
        "MedicalExtractionService.extract",
        side_effect=(
            MedicalExtractionValidationError(
                "Invalid extraction."
            )
        ),
    )
    def test_invalid_extraction_returns_422(
        self,
        mock_extract,
        mock_get,
    ) -> None:
        with self.assertRaises(
            HTTPException
        ) as context:
            generate_document_extraction(
                document_id=(
                    self.document_id
                ),
                request=(
                    ExtractionGenerateRequest()
                ),
                current_user=(
                    self.current_user
                ),
            )

        self.assertEqual(
            context.exception.status_code,
            422,
        )

    @patch(
        "app.api.routes.extractions."
        "MedicalExtractionPersistenceService.get"
    )
    def test_get_uses_authenticated_user(
        self,
        mock_get,
    ) -> None:
        persisted = self._persisted()

        mock_get.return_value = persisted

        result = get_document_extraction(
            document_id=(
                self.document_id
            ),
            current_user=(
                self.current_user
            ),
        )

        self.assertEqual(
            result.extraction_id,
            "extraction-123",
        )

        mock_get.assert_called_once_with(
            document_id=(
                self.document_id
            ),
            user_id="user-123",
        )

    @patch(
        "app.api.routes.extractions."
        "MedicalExtractionPersistenceService.get",
        return_value=None,
    )
    def test_missing_extraction_returns_404(
        self,
        mock_get,
    ) -> None:
        with self.assertRaises(
            HTTPException
        ) as context:
            get_document_extraction(
                document_id=(
                    self.document_id
                ),
                current_user=(
                    self.current_user
                ),
            )

        self.assertEqual(
            context.exception.status_code,
            404,
        )

    @patch(
        "app.api.routes.extractions."
        "MedicalExtractionPersistenceService.delete",
        return_value=True,
    )
    def test_delete_uses_authenticated_user(
        self,
        mock_delete,
    ) -> None:
        result = (
            delete_document_extraction(
                document_id=(
                    self.document_id
                ),
                current_user=(
                    self.current_user
                ),
            )
        )

        self.assertTrue(
            result.deleted
        )

        mock_delete.assert_called_once_with(
            document_id=(
                self.document_id
            ),
            user_id="user-123",
        )

    @patch(
        "app.api.routes.extractions."
        "MedicalExtractionPersistenceService.delete",
        return_value=False,
    )
    def test_delete_missing_extraction_returns_404(
        self,
        mock_delete,
    ) -> None:
        with self.assertRaises(
            HTTPException
        ) as context:
            delete_document_extraction(
                document_id=(
                    self.document_id
                ),
                current_user=(
                    self.current_user
                ),
            )

        self.assertEqual(
            context.exception.status_code,
            404,
        )


if __name__ == "__main__":
    unittest.main()
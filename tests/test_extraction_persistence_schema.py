import unittest
from datetime import datetime

from pydantic import ValidationError

from app.schemas.extraction_persistence import (
    PersistedMedicalExtraction,
)
from app.schemas.medical_extraction import (
    ExtractionMethod,
    ExtractionStatus,
    MedicalDocumentExtraction,
    MedicalDocumentType,
)


class ExtractionPersistenceSchemaTests(
    unittest.TestCase
):
    def test_valid_persisted_extraction(
        self,
    ) -> None:
        extraction = (
            MedicalDocumentExtraction(
                extraction_id=(
                    "extraction-123"
                ),
                document_id=(
                    "document-123"
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

        persisted = (
            PersistedMedicalExtraction(
                extraction_id=(
                    "extraction-123"
                ),
                document_id=(
                    "document-123"
                ),
                schema_version="1.0",
                status=(
                    ExtractionStatus
                    .COMPLETED
                ),
                extraction_method=(
                    ExtractionMethod.HYBRID
                ),
                model_name=(
                    "llama3.2:latest"
                ),
                extraction=extraction,
                created_at=(
                    datetime.utcnow()
                ),
                updated_at=(
                    datetime.utcnow()
                ),
            )
        )

        self.assertEqual(
            persisted.extraction_id,
            "extraction-123",
        )

        self.assertEqual(
            persisted.extraction.document_id,
            "document-123",
        )

    def test_unknown_field_is_rejected(
        self,
    ) -> None:
        extraction = (
            MedicalDocumentExtraction(
                extraction_id=(
                    "extraction-123"
                ),
                document_id=(
                    "document-123"
                ),
                document_type=(
                    MedicalDocumentType
                    .UNKNOWN
                ),
                extraction_confidence=0.0,
            )
        )

        with self.assertRaises(
            ValidationError
        ):
            PersistedMedicalExtraction(
                extraction_id=(
                    "extraction-123"
                ),
                document_id=(
                    "document-123"
                ),
                schema_version="1.0",
                status=(
                    ExtractionStatus
                    .COMPLETED
                ),
                extraction_method=(
                    ExtractionMethod.HYBRID
                ),
                model_name=(
                    "llama3.2:latest"
                ),
                extraction=extraction,
                created_at=(
                    datetime.utcnow()
                ),
                updated_at=(
                    datetime.utcnow()
                ),
                unsupported_field=True,
            )


if __name__ == "__main__":
    unittest.main()
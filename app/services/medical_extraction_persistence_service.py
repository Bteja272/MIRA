from datetime import datetime
from typing import Any
from uuid import uuid4

from pydantic import (
    BaseModel,
    ValidationError,
)
from sqlalchemy import (
    and_,
    delete,
    select,
)
from sqlalchemy.exc import IntegrityError

from app.core.config import settings
from app.db.extraction_models import (
    DocumentExtraction,
)
from app.db.models import Document
from app.db.session import SessionLocal
from app.schemas.extraction_persistence import (
    PersistedMedicalExtraction,
)
from app.schemas.medical_extraction import (
    ExtractionMethod,
    MedicalDocumentExtraction,
)


class MedicalExtractionPersistenceError(
    RuntimeError
):
    pass


class MedicalExtractionPersistenceNotFoundError(
    MedicalExtractionPersistenceError
):
    pass


class MedicalExtractionPersistenceService:
    """
    Store and retrieve one structured extraction per document.

    Save uses one owner-scoped query to verify the document and load an
    existing extraction. Every operation remains scoped by document_id and
    user_id.
    """

    @staticmethod
    def _clean_required_value(
        value: str,
        field_name: str,
    ) -> str:
        cleaned = value.strip()

        if not cleaned:
            raise ValueError(
                f"{field_name} is required."
            )

        return cleaned

    @classmethod
    def _collect_extraction_methods(
        cls,
        value: Any,
        methods: set[ExtractionMethod],
    ) -> None:
        if isinstance(value, BaseModel):
            method = getattr(
                value,
                "extraction_method",
                None,
            )

            if isinstance(
                method,
                ExtractionMethod,
            ):
                methods.add(method)

            for field_name in (
                type(value).model_fields
            ):
                cls._collect_extraction_methods(
                    getattr(
                        value,
                        field_name,
                    ),
                    methods,
                )

            return

        if isinstance(value, list):
            for item in value:
                cls._collect_extraction_methods(
                    item,
                    methods,
                )

            return

        if isinstance(value, dict):
            for item in value.values():
                cls._collect_extraction_methods(
                    item,
                    methods,
                )

    @classmethod
    def _infer_extraction_method(
        cls,
        extraction: MedicalDocumentExtraction,
    ) -> ExtractionMethod:
        methods: set[ExtractionMethod] = set()

        cls._collect_extraction_methods(
            extraction,
            methods,
        )

        if methods == {
            ExtractionMethod.DETERMINISTIC
        }:
            return ExtractionMethod.DETERMINISTIC

        if methods == {
            ExtractionMethod.LLM
        }:
            return ExtractionMethod.LLM

        if methods:
            return ExtractionMethod.HYBRID

        return ExtractionMethod.HYBRID

    @staticmethod
    def _to_response(
        record: DocumentExtraction,
    ) -> PersistedMedicalExtraction:
        try:
            extraction = (
                MedicalDocumentExtraction
                .model_validate(
                    record.extraction_data
                )
            )

        except ValidationError as exc:
            raise MedicalExtractionPersistenceError(
                "The stored extraction contains invalid data."
            ) from exc

        if (
            extraction.document_id
            != record.document_id
        ):
            raise MedicalExtractionPersistenceError(
                "Stored extraction document metadata is inconsistent."
            )

        if (
            extraction.extraction_id
            != record.extraction_id
        ):
            raise MedicalExtractionPersistenceError(
                "Stored extraction identifier is inconsistent."
            )

        return PersistedMedicalExtraction(
            extraction_id=record.extraction_id,
            document_id=record.document_id,
            schema_version=record.schema_version,
            status=record.status,
            extraction_method=(
                record.extraction_method
            ),
            model_name=record.model_name,
            extraction=extraction,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

    @classmethod
    def save(
        cls,
        extraction: MedicalDocumentExtraction,
        user_id: str,
        model_name: str | None = None,
        extraction_method: (
            ExtractionMethod | None
        ) = None,
    ) -> PersistedMedicalExtraction:
        cleaned_document_id = (
            cls._clean_required_value(
                extraction.document_id,
                "document_id",
            )
        )

        cleaned_user_id = (
            cls._clean_required_value(
                user_id,
                "user_id",
            )
        )

        resolved_method = (
            extraction_method
            or cls._infer_extraction_method(
                extraction
            )
        )

        configured_model_name = model_name

        if configured_model_name is None:
            configured_model_name = (
                "deterministic"
                if resolved_method
                == ExtractionMethod.DETERMINISTIC
                else settings.llm_model_name
            )

        cleaned_model_name = (
            cls._clean_required_value(
                configured_model_name,
                "model_name",
            )
        )

        db = SessionLocal()

        try:
            ownership_statement = (
                select(
                    Document.document_id,
                    DocumentExtraction,
                )
                .select_from(Document)
                .outerjoin(
                    DocumentExtraction,
                    and_(
                        DocumentExtraction.document_id
                        == Document.document_id,
                        DocumentExtraction.user_id
                        == Document.user_id,
                    ),
                )
                .where(
                    Document.document_id
                    == cleaned_document_id,
                    Document.user_id
                    == cleaned_user_id,
                )
            )

            row = db.execute(
                ownership_statement
            ).first()

            if row is None:
                raise MedicalExtractionPersistenceNotFoundError(
                    "Document not found."
                )

            record = row[1]
            current_time = datetime.utcnow()

            if record is None:
                extraction_id = str(uuid4())

                stored_extraction = (
                    extraction.model_copy(
                        update={
                            "extraction_id": (
                                extraction_id
                            )
                        }
                    )
                )

                record = DocumentExtraction(
                    extraction_id=extraction_id,
                    document_id=(
                        cleaned_document_id
                    ),
                    user_id=cleaned_user_id,
                    schema_version=(
                        stored_extraction
                        .schema_version
                    ),
                    status=(
                        stored_extraction
                        .status.value
                    ),
                    extraction_method=(
                        resolved_method.value
                    ),
                    model_name=(
                        cleaned_model_name
                    ),
                    extraction_data=(
                        stored_extraction
                        .model_dump(
                            mode="json"
                        )
                    ),
                    created_at=current_time,
                    updated_at=current_time,
                )

                db.add(record)

            else:
                extraction_id = (
                    record.extraction_id
                )

                stored_extraction = (
                    extraction.model_copy(
                        update={
                            "extraction_id": (
                                extraction_id
                            )
                        }
                    )
                )

                record.schema_version = (
                    stored_extraction
                    .schema_version
                )

                record.status = (
                    stored_extraction
                    .status.value
                )

                record.extraction_method = (
                    resolved_method.value
                )

                record.model_name = (
                    cleaned_model_name
                )

                record.extraction_data = (
                    stored_extraction.model_dump(
                        mode="json"
                    )
                )

                record.updated_at = (
                    current_time
                )

            db.commit()
            db.refresh(record)

            return cls._to_response(record)

        except IntegrityError as exc:
            db.rollback()

            raise MedicalExtractionPersistenceError(
                "The structured extraction could not be saved because "
                "its database constraints were violated."
            ) from exc

        except Exception:
            db.rollback()
            raise

        finally:
            db.close()

    @classmethod
    def get(
        cls,
        document_id: str,
        user_id: str,
    ) -> PersistedMedicalExtraction | None:
        cleaned_document_id = (
            cls._clean_required_value(
                document_id,
                "document_id",
            )
        )

        cleaned_user_id = (
            cls._clean_required_value(
                user_id,
                "user_id",
            )
        )

        statement = (
            select(DocumentExtraction)
            .where(
                DocumentExtraction.document_id
                == cleaned_document_id,
                DocumentExtraction.user_id
                == cleaned_user_id,
            )
        )

        db = SessionLocal()

        try:
            record = db.scalar(statement)

            if record is None:
                return None

            return cls._to_response(record)

        finally:
            db.close()

    @classmethod
    def delete(
        cls,
        document_id: str,
        user_id: str,
    ) -> bool:
        cleaned_document_id = (
            cls._clean_required_value(
                document_id,
                "document_id",
            )
        )

        cleaned_user_id = (
            cls._clean_required_value(
                user_id,
                "user_id",
            )
        )

        statement = (
            delete(DocumentExtraction)
            .where(
                DocumentExtraction.document_id
                == cleaned_document_id,
                DocumentExtraction.user_id
                == cleaned_user_id,
            )
        )

        db = SessionLocal()

        try:
            result = db.execute(statement)
            db.commit()

            return bool(result.rowcount)

        except Exception:
            db.rollback()
            raise

        finally:
            db.close()
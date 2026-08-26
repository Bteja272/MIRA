from datetime import datetime
from uuid import uuid4

from pydantic import ValidationError
from sqlalchemy import (
    and_,
    delete,
    select,
)
from sqlalchemy.exc import IntegrityError

from app.db.intelligence_models import (
    DocumentIntelligence,
)
from app.db.models import Document
from app.db.session import SessionLocal
from app.schemas.intelligence_persistence import (
    PersistedMedicalIntelligence,
)
from app.schemas.medical_intelligence import (
    MedicalDocumentIntelligence,
)


class MedicalIntelligencePersistenceError(
    RuntimeError
):
    pass


class MedicalIntelligencePersistenceNotFoundError(
    MedicalIntelligencePersistenceError
):
    pass


class MedicalIntelligencePersistenceService:
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

    @staticmethod
    def _to_response(
        record: DocumentIntelligence,
    ) -> PersistedMedicalIntelligence:
        try:
            intelligence = (
                MedicalDocumentIntelligence
                .model_validate(
                    record.intelligence_data
                )
            )

        except ValidationError as exc:
            raise (
                MedicalIntelligencePersistenceError(
                    "The stored medical intelligence "
                    "contains invalid data."
                )
            ) from exc

        if (
            intelligence.document_id
            != record.document_id
        ):
            raise (
                MedicalIntelligencePersistenceError(
                    "Stored intelligence document "
                    "metadata is inconsistent."
                )
            )

        if (
            intelligence.intelligence_id
            != record.intelligence_id
        ):
            raise (
                MedicalIntelligencePersistenceError(
                    "Stored intelligence identifier "
                    "is inconsistent."
                )
            )

        if (
            intelligence.source_extraction_id
            != record.source_extraction_id
        ):
            raise (
                MedicalIntelligencePersistenceError(
                    "Stored source extraction metadata "
                    "is inconsistent."
                )
            )

        return PersistedMedicalIntelligence(
            intelligence_id=(
                record.intelligence_id
            ),
            document_id=(
                record.document_id
            ),
            source_extraction_id=(
                record.source_extraction_id
            ),
            source_extraction_updated_at=(
                record
                .source_extraction_updated_at
            ),
            schema_version=(
                record.schema_version
            ),
            status=record.status,
            intelligence=intelligence,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

    @classmethod
    def save(
        cls,
        intelligence: (
            MedicalDocumentIntelligence
        ),
        user_id: str,
    ) -> PersistedMedicalIntelligence:
        document_id = (
            cls._clean_required_value(
                intelligence.document_id,
                "document_id",
            )
        )

        cleaned_user_id = (
            cls._clean_required_value(
                user_id,
                "user_id",
            )
        )

        source_extraction_id = (
            cls._clean_required_value(
                intelligence
                .source_extraction_id,
                "source_extraction_id",
            )
        )

        db = SessionLocal()

        try:
            statement = (
                select(
                    Document.document_id,
                    DocumentIntelligence,
                )
                .select_from(Document)
                .outerjoin(
                    DocumentIntelligence,
                    and_(
                        (
                            DocumentIntelligence
                            .document_id
                            == Document
                            .document_id
                        ),
                        (
                            DocumentIntelligence
                            .user_id
                            == Document.user_id
                        ),
                    ),
                )
                .where(
                    Document.document_id
                    == document_id,
                    Document.user_id
                    == cleaned_user_id,
                )
            )

            row = db.execute(
                statement
            ).first()

            if row is None:
                raise (
                    MedicalIntelligencePersistenceNotFoundError(
                        "Document not found."
                    )
                )

            record = row[1]
            now = datetime.utcnow()

            if record is None:
                intelligence_id = str(
                    uuid4()
                )

                stored_intelligence = (
                    intelligence.model_copy(
                        update={
                            "intelligence_id": (
                                intelligence_id
                            )
                        }
                    )
                )

                record = (
                    DocumentIntelligence(
                        intelligence_id=(
                            intelligence_id
                        ),
                        document_id=(
                            document_id
                        ),
                        user_id=(
                            cleaned_user_id
                        ),
                        source_extraction_id=(
                            source_extraction_id
                        ),
                        source_extraction_updated_at=(
                            intelligence
                            .source_extraction_updated_at
                        ),
                        schema_version=(
                            stored_intelligence
                            .schema_version
                        ),
                        status=(
                            stored_intelligence
                            .status
                            .value
                        ),
                        intelligence_data=(
                            stored_intelligence
                            .model_dump(
                                mode="json"
                            )
                        ),
                        created_at=now,
                        updated_at=now,
                    )
                )

                db.add(record)

            else:
                intelligence_id = (
                    record.intelligence_id
                )

                stored_intelligence = (
                    intelligence.model_copy(
                        update={
                            "intelligence_id": (
                                intelligence_id
                            )
                        }
                    )
                )

                record.source_extraction_id = (
                    source_extraction_id
                )

                (
                    record
                    .source_extraction_updated_at
                ) = (
                    intelligence
                    .source_extraction_updated_at
                )

                record.schema_version = (
                    stored_intelligence
                    .schema_version
                )

                record.status = (
                    stored_intelligence
                    .status
                    .value
                )

                record.intelligence_data = (
                    stored_intelligence
                    .model_dump(
                        mode="json"
                    )
                )

                record.updated_at = now

            db.commit()
            db.refresh(record)

            return cls._to_response(
                record
            )

        except IntegrityError as exc:
            db.rollback()

            raise (
                MedicalIntelligencePersistenceError(
                    "The medical intelligence could "
                    "not be saved because database "
                    "constraints were violated."
                )
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
    ) -> (
        PersistedMedicalIntelligence
        | None
    ):
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
            select(
                DocumentIntelligence
            )
            .where(
                (
                    DocumentIntelligence
                    .document_id
                    == cleaned_document_id
                ),
                (
                    DocumentIntelligence
                    .user_id
                    == cleaned_user_id
                ),
            )
        )

        db = SessionLocal()

        try:
            record = db.scalar(
                statement
            )

            if record is None:
                return None

            return cls._to_response(
                record
            )

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
            delete(
                DocumentIntelligence
            )
            .where(
                (
                    DocumentIntelligence
                    .document_id
                    == cleaned_document_id
                ),
                (
                    DocumentIntelligence
                    .user_id
                    == cleaned_user_id
                ),
            )
        )

        db = SessionLocal()

        try:
            result = db.execute(
                statement
            )

            db.commit()

            return bool(
                result.rowcount
            )

        except Exception:
            db.rollback()
            raise

        finally:
            db.close()
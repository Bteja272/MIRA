from pathlib import Path
from uuid import uuid4

from sqlalchemy import func, select

from app.db.models import (
    Document,
    DocumentChunk,
)
from app.db.session import SessionLocal


class DocumentService:
    @staticmethod
    def _apply_user_scope(
        statement,
        user_id: str | None,
    ):
        """
        Restrict document operations to one user.

        During local development, documents have user_id=None.
        Authentication will later replace this with the
        authenticated user's ID.
        """
        if user_id is None:
            return statement.where(
                Document.user_id.is_(None)
            )

        return statement.where(
            Document.user_id == user_id
        )

    @staticmethod
    def _chunk_count_subquery():
        return (
            select(
                func.count(
                    DocumentChunk.id
                )
            )
            .where(
                DocumentChunk.document_id
                == Document.document_id
            )
            .correlate(Document)
            .scalar_subquery()
        )

    @staticmethod
    def _to_response(
        document: Document,
        chunk_count: int,
    ) -> dict:
        return {
            "document_id": (
                document.document_id
            ),
            "filename": (
                document.original_filename
            ),
            "document_type": (
                document.document_type
            ),
            "file_size_bytes": (
                document.file_size_bytes
            ),
            "chunk_count": chunk_count,
            "uploaded_at": (
                document.created_at.isoformat()
                if document.created_at
                else None
            ),
        }

    @classmethod
    def list_documents(
        cls,
        user_id: str | None = None,
    ) -> list[dict]:
        chunk_count = (
            cls._chunk_count_subquery()
            .label("chunk_count")
        )

        statement = select(
            Document,
            chunk_count,
        )

        statement = cls._apply_user_scope(
            statement=statement,
            user_id=user_id,
        )

        statement = statement.order_by(
            Document.created_at.desc(),
            Document.id.desc(),
        )

        db = SessionLocal()

        try:
            rows = db.execute(
                statement
            ).all()

            return [
                cls._to_response(
                    document=document,
                    chunk_count=int(
                        row_chunk_count or 0
                    ),
                )
                for (
                    document,
                    row_chunk_count,
                ) in rows
            ]

        finally:
            db.close()

    @classmethod
    def get_document(
        cls,
        document_id: str,
        user_id: str | None = None,
    ) -> dict | None:
        chunk_count = (
            cls._chunk_count_subquery()
            .label("chunk_count")
        )

        statement = (
            select(
                Document,
                chunk_count,
            )
            .where(
                Document.document_id
                == document_id
            )
        )

        statement = cls._apply_user_scope(
            statement=statement,
            user_id=user_id,
        )

        db = SessionLocal()

        try:
            row = db.execute(
                statement
            ).one_or_none()

            if row is None:
                return None

            document, row_chunk_count = row

            response = cls._to_response(
                document=document,
                chunk_count=int(
                    row_chunk_count or 0
                ),
            )

            response.update(
                {
                    "source": (
                        document.source
                    ),
                    "file_hash": (
                        document.file_hash
                    ),
                }
            )

            return response

        finally:
            db.close()

    @classmethod
    def get_existing_document_ids(
        cls,
        document_ids: list[str],
        user_id: str | None = None,
    ) -> list[str]:
        """
        Return selected document IDs that exist in the
        current user's document scope.
        """
        if not document_ids:
            return []

        statement = (
            select(
                Document.document_id
            )
            .where(
                Document.document_id.in_(
                    document_ids
                )
            )
        )

        statement = cls._apply_user_scope(
            statement=statement,
            user_id=user_id,
        )

        db = SessionLocal()

        try:
            found_ids = set(
                db.scalars(
                    statement
                ).all()
            )

            # Preserve the order selected by the caller.
            return [
                document_id
                for document_id
                in document_ids
                if document_id in found_ids
            ]

        finally:
            db.close()

    @classmethod
    def find_duplicate_by_hash(
        cls,
        file_hash: str,
        user_id: str | None = None,
    ) -> dict | None:
        statement = (
            select(Document)
            .where(
                Document.file_hash
                == file_hash
            )
        )

        statement = cls._apply_user_scope(
            statement=statement,
            user_id=user_id,
        )

        statement = (
            statement
            .order_by(
                Document.created_at.desc()
            )
            .limit(1)
        )

        db = SessionLocal()

        try:
            document = db.scalar(
                statement
            )

            if document is None:
                return None

            return {
                "document_id": (
                    document.document_id
                ),
                "filename": (
                    document.original_filename
                ),
                "document_type": (
                    document.document_type
                ),
                "uploaded_at": (
                    document.created_at
                    .isoformat()
                    if document.created_at
                    else None
                ),
            }

        finally:
            db.close()

    @staticmethod
    def _resolve_stored_path(
        upload_directory: Path,
        stored_filename: str,
    ) -> Path:
        if not stored_filename:
            raise ValueError(
                "Stored filename is missing."
            )

        if (
            "/" in stored_filename
            or "\\" in stored_filename
            or Path(stored_filename).name
            != stored_filename
        ):
            raise ValueError(
                "Unsafe stored filename."
            )

        base_directory = (
            upload_directory.resolve()
        )

        stored_path = (
            base_directory
            / stored_filename
        ).resolve()

        if (
            stored_path.parent
            != base_directory
        ):
            raise ValueError(
                "Stored file is outside "
                "the upload directory."
            )

        return stored_path

    @classmethod
    def delete_document(
        cls,
        document_id: str,
        upload_directory: Path,
        user_id: str | None = None,
    ) -> dict | None:
        """
        Permanently delete the document, its chunks,
        embeddings, and physical stored file.

        Chunk rows are removed through ON DELETE CASCADE.
        """
        statement = (
            select(Document)
            .where(
                Document.document_id
                == document_id
            )
        )

        statement = cls._apply_user_scope(
            statement=statement,
            user_id=user_id,
        )

        db = SessionLocal()

        original_path: Path | None = None
        staged_path: Path | None = None

        try:
            document = db.scalar(
                statement
            )

            if document is None:
                return None

            original_filename = (
                document.original_filename
            )

            if document.stored_filename:
                original_path = (
                    cls._resolve_stored_path(
                        upload_directory=(
                            upload_directory
                        ),
                        stored_filename=(
                            document.stored_filename
                        ),
                    )
                )

            if (
                original_path is not None
                and original_path.exists()
            ):
                staged_path = (
                    original_path.with_name(
                        (
                            f".{original_path.name}."
                            f"{uuid4().hex}."
                            "deleting"
                        )
                    )
                )

                original_path.replace(
                    staged_path
                )

            db.delete(document)
            db.commit()

        except Exception:
            db.rollback()

            if (
                staged_path is not None
                and staged_path.exists()
                and original_path is not None
                and not original_path.exists()
            ):
                staged_path.replace(
                    original_path
                )

            raise

        finally:
            db.close()

        file_deleted = True

        if (
            staged_path is not None
            and staged_path.exists()
        ):
            try:
                staged_path.unlink()

            except OSError as exc:
                file_deleted = False

                raise RuntimeError(
                    "Database records were deleted, "
                    "but the physical file could "
                    "not be removed."
                ) from exc

        return {
            "document_id": document_id,
            "filename": original_filename,
            "deleted": True,
            "file_deleted": file_deleted,
        }
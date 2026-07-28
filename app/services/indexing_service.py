from app.db.models import (
    Document,
    DocumentChunk,
)
from app.db.session import SessionLocal
from app.services.embedding_service import (
    EmbeddingService,
)


class IndexingService:
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
    def index_document(
        cls,
        *,
        document_id: str,
        source: str,
        original_filename: str,
        stored_filename: str,
        document_type: str,
        file_hash: str,
        file_size_bytes: int,
        chunk_records: list[dict],
        user_id: str,
    ) -> int:
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

        if not chunk_records:
            raise ValueError(
                "No document chunks were produced for indexing."
            )

        chunk_ids = [
            str(record["chunk_id"])
            for record in chunk_records
        ]

        if len(chunk_ids) != len(set(chunk_ids)):
            raise ValueError(
                "Duplicate chunk identifiers were produced."
            )

        texts = [
            str(record["text"])
            for record in chunk_records
        ]

        embeddings = (
            EmbeddingService.embed_texts(
                texts
            )
        )

        if len(embeddings) != len(chunk_records):
            raise RuntimeError(
                "Embedding count does not match chunk count."
            )

        document = Document(
            document_id=cleaned_document_id,
            user_id=cleaned_user_id,
            source=source,
            original_filename=(
                original_filename
            ),
            stored_filename=stored_filename,
            document_type=document_type,
            file_hash=file_hash,
            file_size_bytes=file_size_bytes,
        )

        chunk_models = [
            DocumentChunk(
                chunk_id=record["chunk_id"],
                document_id=(
                    cleaned_document_id
                ),
                page_number=record.get(
                    "page_number"
                ),
                chunk_index=record[
                    "chunk_index"
                ],
                text=record["text"],
                embedding=embedding,
            )
            for record, embedding in zip(
                chunk_records,
                embeddings,
                strict=True,
            )
        ]

        db = SessionLocal()

        try:
            db.add(document)
            db.flush()
            db.add_all(chunk_models)
            db.commit()

            return len(chunk_models)

        except Exception:
            db.rollback()
            raise

        finally:
            db.close()
from app.db.models import Document, DocumentChunk
from app.db.session import SessionLocal
from app.services.embedding_service import EmbeddingService


class IndexingService:
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
        user_id: str | None = None,
    ) -> int:
        if not chunk_records:
            raise ValueError(
                "No document chunks were produced for indexing."
            )

        texts = [
            record["text"]
            for record in chunk_records
        ]

        embeddings = EmbeddingService.embed_texts(
            texts
        )

        if len(embeddings) != len(chunk_records):
            raise RuntimeError(
                "Embedding count does not match chunk count."
            )

        db = SessionLocal()

        try:
            document = Document(
                document_id=document_id,
                user_id=user_id,
                source=source,
                original_filename=original_filename,
                stored_filename=stored_filename,
                document_type=document_type,
                file_hash=file_hash,
                file_size_bytes=file_size_bytes,
            )

            db.add(document)
            db.flush()

            for record, embedding in zip(
                chunk_records,
                embeddings,
                strict=True,
            ):
                db.add(
                    DocumentChunk(
                        chunk_id=record["chunk_id"],
                        document_id=document_id,
                        page_number=record.get(
                            "page_number"
                        ),
                        chunk_index=record["chunk_index"],
                        text=record["text"],
                        embedding=embedding,
                    )
                )

            db.commit()

            return len(chunk_records)

        except Exception:
            db.rollback()
            raise

        finally:
            db.close()
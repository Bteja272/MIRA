from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Document, DocumentChunk
from app.db.session import SessionLocal
from app.services.embedding_service import EmbeddingService


class RetrievalService:
    @staticmethod
    def retrieve(
        query: str,
        top_k: int = 3,
        document_id: str | None = None,
    ) -> list[dict]:
        query_embedding = EmbeddingService.embed_text(query)
        distance = DocumentChunk.embedding.cosine_distance(
            query_embedding
        ).label("distance")

        db: Session = SessionLocal()

        try:
            stmt = (
                select(
                    DocumentChunk,
                    Document.source,
                    distance,
                )
                .join(
                    Document,
                    Document.document_id == DocumentChunk.document_id,
                )
                .where(DocumentChunk.embedding.is_not(None))
            )

            if document_id:
                stmt = stmt.where(
                    DocumentChunk.document_id == document_id
                )

            stmt = stmt.order_by(distance).limit(top_k)

            rows = db.execute(stmt).all()

            results = []

            for chunk, source, distance_value in rows:
                similarity_score = 1.0 - float(distance_value)

                results.append(
                    {
                        "chunk_id": chunk.chunk_id,
                        "document_id": chunk.document_id,
                        "source": Path(source).name,
                        "page_number": chunk.page_number,
                        "chunk_index": chunk.chunk_index,
                        "text": chunk.text,
                        "similarity_score": round(
                            similarity_score,
                            4,
                        ),
                    }
                )

            return results

        finally:
            db.close()

    @staticmethod
    def retrieve_document(document_id: str) -> list[dict]:
        """
        Retrieve every chunk belonging to one document in its
        original reading order.
        """
        db: Session = SessionLocal()

        try:
            stmt = (
                select(
                    DocumentChunk,
                    Document.source,
                )
                .join(
                    Document,
                    Document.document_id == DocumentChunk.document_id,
                )
                .where(DocumentChunk.document_id == document_id)
                .order_by(
                    DocumentChunk.page_number.asc().nullsfirst(),
                    DocumentChunk.chunk_index.asc(),
                )
            )

            rows = db.execute(stmt).all()

            return [
                {
                    "chunk_id": chunk.chunk_id,
                    "document_id": chunk.document_id,
                    "source": Path(source).name,
                    "page_number": chunk.page_number,
                    "chunk_index": chunk.chunk_index,
                    "text": chunk.text,
                    "similarity_score": None,
                }
                for chunk, source in rows
            ]

        finally:
            db.close()

    @staticmethod
    def get_latest_document_id() -> str | None:
        db: Session = SessionLocal()

        try:
            stmt = (
                select(Document.document_id)
                .order_by(
                    Document.created_at.desc(),
                    Document.id.desc(),
                )
                .limit(1)
            )

            return db.execute(stmt).scalar_one_or_none()

        finally:
            db.close()
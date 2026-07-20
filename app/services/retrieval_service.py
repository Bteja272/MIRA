from pathlib import Path

from sqlalchemy import select

from app.db.models import (
    Document,
    DocumentChunk,
)
from app.db.session import SessionLocal
from app.services.embedding_service import (
    EmbeddingService,
)


class RetrievalService:
    @staticmethod
    def _normalize_document_ids(
        document_id: str | None = None,
        document_ids: list[str] | None = None,
    ) -> list[str]:
        selected: list[str] = []
        candidates: list[str] = []

        if document_id:
            candidates.append(
                document_id
            )

        if document_ids:
            candidates.extend(
                document_ids
            )

        for candidate in candidates:
            cleaned = candidate.strip()

            if (
                cleaned
                and cleaned not in selected
            ):
                selected.append(cleaned)

        return selected

    @staticmethod
    def _apply_user_scope(
        statement,
        user_id: str | None,
    ):
        if user_id is None:
            return statement.where(
                Document.user_id.is_(None)
            )

        return statement.where(
            Document.user_id == user_id
        )

    @staticmethod
    def _to_result(
        chunk: DocumentChunk,
        document: Document,
        similarity_score: float | None,
        document_position: int | None = None,
    ) -> dict:
        source = (
            document.original_filename
            or document.source
            or Path(
                document.stored_filename
            ).name
        )

        return {
            "chunk_id": chunk.chunk_id,
            "document_id": (
                chunk.document_id
            ),
            "source": source,
            "document_type": (
                document.document_type
            ),
            "page_number": (
                chunk.page_number
            ),
            "chunk_index": (
                chunk.chunk_index
            ),
            "similarity_score": (
                similarity_score
            ),
            "document_position": (
                document_position
            ),
            "text": chunk.text,
        }

    @classmethod
    def retrieve(
        cls,
        query: str,
        top_k: int,
        document_id: str | None = None,
        document_ids: list[str] | None = None,
        user_id: str | None = None,
    ) -> list[dict]:
        selected_ids = (
            cls._normalize_document_ids(
                document_id=document_id,
                document_ids=document_ids,
            )
        )

        query_embedding = (
            EmbeddingService.embed_text(
                query
            )
        )

        distance_expression = (
            DocumentChunk.embedding
            .cosine_distance(
                query_embedding
            )
            .label("distance")
        )

        statement = (
            select(
                DocumentChunk,
                Document,
                distance_expression,
            )
            .join(
                Document,
                Document.document_id
                == DocumentChunk.document_id,
            )
        )

        statement = cls._apply_user_scope(
            statement=statement,
            user_id=user_id,
        )

        if selected_ids:
            statement = statement.where(
                DocumentChunk.document_id
                .in_(selected_ids)
            )

        statement = (
            statement
            .order_by(
                distance_expression.asc()
            )
            .limit(top_k)
        )

        db = SessionLocal()

        try:
            rows = db.execute(
                statement
            ).all()

            results: list[dict] = []

            for (
                chunk,
                document,
                distance,
            ) in rows:
                numeric_distance = (
                    float(distance)
                    if distance is not None
                    else None
                )

                similarity_score = None

                if numeric_distance is not None:
                    similarity_score = round(
                        max(
                            0.0,
                            min(
                                1.0,
                                1.0
                                - numeric_distance,
                            ),
                        ),
                        4,
                    )

                document_position = None

                if selected_ids:
                    document_position = (
                        selected_ids.index(
                            chunk.document_id
                        )
                        + 1
                    )

                results.append(
                    cls._to_result(
                        chunk=chunk,
                        document=document,
                        similarity_score=(
                            similarity_score
                        ),
                        document_position=(
                            document_position
                        ),
                    )
                )

            return results

        finally:
            db.close()

    @classmethod
    def retrieve_document(
        cls,
        document_id: str,
        user_id: str | None = None,
        document_position: (
            int | None
        ) = None,
    ) -> list[dict]:
        statement = (
            select(
                DocumentChunk,
                Document,
            )
            .join(
                Document,
                Document.document_id
                == DocumentChunk.document_id,
            )
            .where(
                DocumentChunk.document_id
                == document_id
            )
        )

        statement = cls._apply_user_scope(
            statement=statement,
            user_id=user_id,
        )

        statement = statement.order_by(
            DocumentChunk.page_number
            .asc()
            .nullsfirst(),
            DocumentChunk.chunk_index.asc(),
        )

        db = SessionLocal()

        try:
            rows = db.execute(
                statement
            ).all()

            return [
                cls._to_result(
                    chunk=chunk,
                    document=document,
                    similarity_score=None,
                    document_position=(
                        document_position
                    ),
                )
                for chunk, document in rows
            ]

        finally:
            db.close()

    @classmethod
    def retrieve_documents(
        cls,
        document_ids: list[str],
        user_id: str | None = None,
    ) -> list[dict]:
        results: list[dict] = []

        for (
            position,
            document_id,
        ) in enumerate(
            document_ids,
            start=1,
        ):
            document_results = (
                cls.retrieve_document(
                    document_id=document_id,
                    user_id=user_id,
                    document_position=(
                        position
                    ),
                )
            )

            results.extend(
                document_results
            )

        return results

    @classmethod
    def get_latest_document_id(
        cls,
        user_id: str | None = None,
    ) -> str | None:
        statement = select(
            Document.document_id
        )

        statement = cls._apply_user_scope(
            statement=statement,
            user_id=user_id,
        )

        statement = (
            statement
            .order_by(
                Document.created_at.desc(),
                Document.id.desc(),
            )
            .limit(1)
        )

        db = SessionLocal()

        try:
            return db.scalar(
                statement
            )

        finally:
            db.close()
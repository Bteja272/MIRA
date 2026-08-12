import logging
from pathlib import Path
from time import perf_counter

from sqlalchemy import select

from app.core.config import settings
from app.db.models import (
    Document,
    DocumentChunk,
)
from app.db.session import SessionLocal
from app.services.bm25_service import (
    BM25Service,
)
from app.services.embedding_service import (
    EmbeddingService,
)


logger = logging.getLogger(__name__)


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
    def _document_position_map(
        selected_ids: list[str],
    ) -> dict[str, int]:
        return {
            document_id: position
            for position, document_id
            in enumerate(
                selected_ids,
                start=1,
            )
        }

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
    def _retrieve_semantic_candidates(
        cls,
        *,
        query: str,
        candidate_k: int,
        selected_ids: list[str],
        user_id: str | None,
    ) -> list[dict]:
        started_at = perf_counter()

        model_was_warm = (
            EmbeddingService
            .is_model_loaded()
        )

        embedding_started_at = (
            perf_counter()
        )
        query_embedding = (
            EmbeddingService.embed_text(
                query
            )
        )
        query_embedding_ms = (
            perf_counter()
            - embedding_started_at
        ) * 1000

        statement_started_at = (
            perf_counter()
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
            .limit(candidate_k)
        )

        statement_build_ms = (
            perf_counter()
            - statement_started_at
        ) * 1000

        db = SessionLocal()

        try:
            search_started_at = (
                perf_counter()
            )
            rows = db.execute(
                statement
            ).all()
            vector_search_ms = (
                perf_counter()
                - search_started_at
            ) * 1000

            result_build_started_at = (
                perf_counter()
            )

            position_map = (
                cls._document_position_map(
                    selected_ids
                )
            )

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

                if (
                    numeric_distance
                    is not None
                ):
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

                result = cls._to_result(
                    chunk=chunk,
                    document=document,
                    similarity_score=(
                        similarity_score
                    ),
                    document_position=(
                        position_map.get(
                            chunk.document_id
                        )
                    ),
                )

                result["semantic_rank"] = (
                    len(results) + 1
                )
                result["lexical_rank"] = None
                result["lexical_score"] = None
                result["hybrid_score"] = None
                result["retrieval_method"] = (
                    "semantic"
                )

                results.append(result)

            result_build_ms = (
                perf_counter()
                - result_build_started_at
            ) * 1000

            total_ms = (
                perf_counter()
                - started_at
            ) * 1000

            logger.info(
                "retrieval_vector_completed "
                "selected_count=%s "
                "candidate_k=%s "
                "result_count=%s "
                "embedding_model_was_warm=%s "
                "query_embedding_ms=%.3f "
                "statement_build_ms=%.3f "
                "vector_search_ms=%.3f "
                "result_build_ms=%.3f "
                "total_ms=%.3f",
                len(selected_ids),
                candidate_k,
                len(results),
                model_was_warm,
                query_embedding_ms,
                statement_build_ms,
                vector_search_ms,
                result_build_ms,
                total_ms,
            )

            return results

        finally:
            db.close()

    @classmethod
    def _retrieve_lexical_candidates(
        cls,
        *,
        query: str,
        candidate_k: int,
        selected_ids: list[str],
        user_id: str | None,
    ) -> list[dict]:
        started_at = perf_counter()

        statement_started_at = (
            perf_counter()
        )

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
                Document.created_at.desc(),
                DocumentChunk.id.asc(),
            )
            .limit(
                settings
                .retrieval_lexical_max_chunks
            )
        )

        statement_build_ms = (
            perf_counter()
            - statement_started_at
        ) * 1000

        db = SessionLocal()

        try:
            load_started_at = (
                perf_counter()
            )
            rows = db.execute(
                statement
            ).all()
            corpus_load_ms = (
                perf_counter()
                - load_started_at
            ) * 1000

            if not rows:
                logger.info(
                    "retrieval_lexical_completed "
                    "selected_count=%s "
                    "candidate_k=%s "
                    "corpus_count=0 "
                    "result_count=0 "
                    "statement_build_ms=%.3f "
                    "corpus_load_ms=%.3f "
                    "bm25_score_ms=0.000 "
                    "result_build_ms=0.000 "
                    "total_ms=%.3f",
                    len(selected_ids),
                    candidate_k,
                    statement_build_ms,
                    corpus_load_ms,
                    (
                        perf_counter()
                        - started_at
                    )
                    * 1000,
                )
                return []

            texts = [
                chunk.text
                for chunk, _document
                in rows
            ]

            score_started_at = (
                perf_counter()
            )
            ranked = BM25Service.rank(
                query=query,
                documents=texts,
                top_k=candidate_k,
                k1=(
                    settings
                    .retrieval_bm25_k1
                ),
                b=(
                    settings
                    .retrieval_bm25_b
                ),
            )
            bm25_score_ms = (
                perf_counter()
                - score_started_at
            ) * 1000

            result_build_started_at = (
                perf_counter()
            )

            position_map = (
                cls._document_position_map(
                    selected_ids
                )
            )

            results: list[dict] = []

            for (
                lexical_rank,
                (
                    corpus_index,
                    lexical_score,
                ),
            ) in enumerate(
                ranked,
                start=1,
            ):
                (
                    chunk,
                    document,
                ) = rows[corpus_index]

                result = cls._to_result(
                    chunk=chunk,
                    document=document,
                    similarity_score=None,
                    document_position=(
                        position_map.get(
                            chunk.document_id
                        )
                    ),
                )

                result["semantic_rank"] = None
                result["lexical_rank"] = (
                    lexical_rank
                )
                result["lexical_score"] = (
                    round(
                        lexical_score,
                        6,
                    )
                )
                result["hybrid_score"] = None
                result["retrieval_method"] = (
                    "lexical"
                )

                results.append(result)

            result_build_ms = (
                perf_counter()
                - result_build_started_at
            ) * 1000

            total_ms = (
                perf_counter()
                - started_at
            ) * 1000

            logger.info(
                "retrieval_lexical_completed "
                "selected_count=%s "
                "candidate_k=%s "
                "corpus_count=%s "
                "result_count=%s "
                "statement_build_ms=%.3f "
                "corpus_load_ms=%.3f "
                "bm25_score_ms=%.3f "
                "result_build_ms=%.3f "
                "total_ms=%.3f",
                len(selected_ids),
                candidate_k,
                len(rows),
                len(results),
                statement_build_ms,
                corpus_load_ms,
                bm25_score_ms,
                result_build_ms,
                total_ms,
            )

            return results

        finally:
            db.close()

    @classmethod
    def _fuse_candidates(
        cls,
        *,
        semantic_candidates: list[dict],
        lexical_candidates: list[dict],
        top_k: int,
    ) -> list[dict]:
        if top_k <= 0:
            return []

        rrf_k = settings.retrieval_rrf_k
        semantic_weight = (
            settings
            .retrieval_semantic_weight
        )
        lexical_weight = (
            settings
            .retrieval_lexical_weight
        )

        fused: dict[str, dict] = {}

        for (
            semantic_rank,
            candidate,
        ) in enumerate(
            semantic_candidates,
            start=1,
        ):
            chunk_id = candidate[
                "chunk_id"
            ]

            fused[chunk_id] = {
                **candidate,
                "semantic_rank": (
                    semantic_rank
                ),
                "lexical_rank": None,
                "lexical_score": None,
                "hybrid_score": (
                    semantic_weight
                    / (
                        rrf_k
                        + semantic_rank
                    )
                ),
                "retrieval_method": (
                    "hybrid"
                ),
            }

        for (
            lexical_rank,
            candidate,
        ) in enumerate(
            lexical_candidates,
            start=1,
        ):
            chunk_id = candidate[
                "chunk_id"
            ]

            lexical_contribution = (
                lexical_weight
                / (
                    rrf_k
                    + lexical_rank
                )
            )

            if chunk_id in fused:
                existing = fused[
                    chunk_id
                ]

                existing[
                    "lexical_rank"
                ] = lexical_rank
                existing[
                    "lexical_score"
                ] = candidate.get(
                    "lexical_score"
                )
                existing[
                    "hybrid_score"
                ] += (
                    lexical_contribution
                )

            else:
                fused[chunk_id] = {
                    **candidate,
                    "semantic_rank": None,
                    "lexical_rank": (
                        lexical_rank
                    ),
                    "hybrid_score": (
                        lexical_contribution
                    ),
                    "retrieval_method": (
                        "hybrid"
                    ),
                }

        ranked_results = list(
            fused.values()
        )

        ranked_results.sort(
            key=lambda result: (
                -float(
                    result.get(
                        "hybrid_score",
                        0.0,
                    )
                ),
                (
                    result.get(
                        "semantic_rank"
                    )
                    if result.get(
                        "semantic_rank"
                    )
                    is not None
                    else 10**9
                ),
                (
                    result.get(
                        "lexical_rank"
                    )
                    if result.get(
                        "lexical_rank"
                    )
                    is not None
                    else 10**9
                ),
                str(
                    result.get(
                        "chunk_id",
                        "",
                    )
                ),
            )
        )

        final_results = (
            ranked_results[:top_k]
        )

        for result in final_results:
            result["hybrid_score"] = round(
                float(
                    result[
                        "hybrid_score"
                    ]
                ),
                8,
            )

        return final_results

    @classmethod
    def retrieve(
        cls,
        query: str,
        top_k: int,
        document_id: str | None = None,
        document_ids: list[str] | None = None,
        user_id: str | None = None,
    ) -> list[dict]:
        started_at = perf_counter()

        selected_ids = (
            cls._normalize_document_ids(
                document_id=document_id,
                document_ids=document_ids,
            )
        )

        candidate_k = max(
            top_k,
            settings.retrieval_candidate_k,
        )

        semantic_started_at = (
            perf_counter()
        )
        semantic_candidates = (
            cls
            ._retrieve_semantic_candidates(
                query=query,
                candidate_k=candidate_k,
                selected_ids=selected_ids,
                user_id=user_id,
            )
        )
        semantic_ms = (
            perf_counter()
            - semantic_started_at
        ) * 1000

        lexical_started_at = (
            perf_counter()
        )
        lexical_candidates = (
            cls
            ._retrieve_lexical_candidates(
                query=query,
                candidate_k=candidate_k,
                selected_ids=selected_ids,
                user_id=user_id,
            )
        )
        lexical_ms = (
            perf_counter()
            - lexical_started_at
        ) * 1000

        fusion_started_at = (
            perf_counter()
        )
        results = cls._fuse_candidates(
            semantic_candidates=(
                semantic_candidates
            ),
            lexical_candidates=(
                lexical_candidates
            ),
            top_k=top_k,
        )
        fusion_ms = (
            perf_counter()
            - fusion_started_at
        ) * 1000

        total_ms = (
            perf_counter()
            - started_at
        ) * 1000

        logger.info(
            "retrieval_hybrid_completed "
            "selected_count=%s "
            "top_k=%s candidate_k=%s "
            "semantic_candidate_count=%s "
            "lexical_candidate_count=%s "
            "result_count=%s "
            "semantic_ms=%.3f "
            "lexical_ms=%.3f "
            "fusion_ms=%.3f "
            "total_ms=%.3f",
            len(selected_ids),
            top_k,
            candidate_k,
            len(semantic_candidates),
            len(lexical_candidates),
            len(results),
            semantic_ms,
            lexical_ms,
            fusion_ms,
            total_ms,
        )

        return results

    @classmethod
    def retrieve_document(
        cls,
        document_id: str,
        user_id: str | None = None,
        document_position: (
            int | None
        ) = None,
    ) -> list[dict]:
        started_at = perf_counter()

        statement_started_at = (
            perf_counter()
        )

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

        statement_build_ms = (
            perf_counter()
            - statement_started_at
        ) * 1000

        db = SessionLocal()

        try:
            load_started_at = (
                perf_counter()
            )
            rows = db.execute(
                statement
            ).all()
            document_load_ms = (
                perf_counter()
                - load_started_at
            ) * 1000

            result_build_started_at = (
                perf_counter()
            )
            results = [
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
            result_build_ms = (
                perf_counter()
                - result_build_started_at
            ) * 1000

            total_ms = (
                perf_counter()
                - started_at
            ) * 1000

            logger.info(
                "retrieval_document_completed "
                "chunk_count=%s "
                "document_position=%s "
                "statement_build_ms=%.3f "
                "document_load_ms=%.3f "
                "result_build_ms=%.3f "
                "total_ms=%.3f",
                len(results),
                document_position,
                statement_build_ms,
                document_load_ms,
                result_build_ms,
                total_ms,
            )

            return results

        finally:
            db.close()

    @classmethod
    def retrieve_documents(
        cls,
        document_ids: list[str],
        user_id: str | None = None,
    ) -> list[dict]:
        started_at = perf_counter()
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

        total_ms = (
            perf_counter()
            - started_at
        ) * 1000

        logger.info(
            "retrieval_documents_completed "
            "document_count=%s "
            "chunk_count=%s total_ms=%.3f",
            len(document_ids),
            len(results),
            total_ms,
        )

        return results

    @classmethod
    def get_latest_document_id(
        cls,
        user_id: str | None = None,
    ) -> str | None:
        started_at = perf_counter()

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
            document_id = db.scalar(
                statement
            )

            logger.info(
                "retrieval_latest_document_completed "
                "found=%s total_ms=%.3f",
                document_id is not None,
                (
                    perf_counter()
                    - started_at
                )
                * 1000,
            )

            return document_id

        finally:
            db.close()
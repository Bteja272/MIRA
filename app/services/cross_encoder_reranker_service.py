import logging
from time import perf_counter

from sentence_transformers import (
    CrossEncoder,
)

from app.core.config import settings


logger = logging.getLogger(__name__)


class CrossEncoderRerankerService:
    _model: CrossEncoder | None = None

    @classmethod
    def is_model_loaded(cls) -> bool:
        return cls._model is not None

    @classmethod
    def get_model(cls) -> CrossEncoder:
        if cls._model is None:
            started_at = perf_counter()

            configured_device = (
                settings
                .retrieval_reranker_device
                .strip()
            )

            cls._model = CrossEncoder(
                settings
                .retrieval_reranker_model_name,
                device=(
                    configured_device
                    or None
                ),
            )

            logger.info(
                "reranker_model_loaded "
                "model=%s device=%s "
                "load_ms=%.3f",
                settings
                .retrieval_reranker_model_name,
                configured_device
                or "auto",
                (
                    perf_counter()
                    - started_at
                )
                * 1000,
            )

        return cls._model

    @staticmethod
    def _normalize_score(
        score,
    ) -> float:
        if hasattr(
            score,
            "tolist",
        ):
            score = score.tolist()

        while isinstance(
            score,
            (list, tuple),
        ):
            if not score:
                return 0.0

            score = score[0]

        return float(score)

    @classmethod
    def rerank(
        cls,
        *,
        query: str,
        candidates: list[dict],
        top_k: int,
    ) -> list[dict]:
        if top_k <= 0:
            return []

        if not candidates:
            return []

        model_was_warm = (
            cls.is_model_loaded()
        )
        started_at = perf_counter()

        model = cls.get_model()

        pairs = [
            (
                query,
                str(
                    candidate.get(
                        "text",
                        "",
                    )
                ),
            )
            for candidate in candidates
        ]

        predict_started_at = (
            perf_counter()
        )

        raw_scores = model.predict(
            pairs,
            batch_size=(
                settings
                .retrieval_reranker_batch_size
            ),
            show_progress_bar=False,
            convert_to_numpy=True,
        )

        predict_ms = (
            perf_counter()
            - predict_started_at
        ) * 1000

        scores = [
            cls._normalize_score(
                score
            )
            for score in raw_scores
        ]

        scored_candidates: list[
            tuple[int, float, dict]
        ] = []

        for (
            original_rank,
            (
                candidate,
                score,
            ),
        ) in enumerate(
            zip(
                candidates,
                scores,
                strict=True,
            ),
            start=1,
        ):
            scored_candidates.append(
                (
                    original_rank,
                    score,
                    candidate,
                )
            )

        scored_candidates.sort(
            key=lambda item: (
                -item[1],
                -float(
                    item[2].get(
                        "hybrid_score",
                        0.0,
                    )
                ),
                item[0],
            )
        )

        results: list[dict] = []

        for (
            rerank_rank,
            (
                _original_rank,
                score,
                candidate,
            ),
        ) in enumerate(
            scored_candidates[:top_k],
            start=1,
        ):
            results.append(
                {
                    **candidate,
                    "rerank_rank": (
                        rerank_rank
                    ),
                    "rerank_score": round(
                        score,
                        6,
                    ),
                    "retrieval_method": (
                        "hybrid_reranked"
                    ),
                }
            )

        total_ms = (
            perf_counter()
            - started_at
        ) * 1000

        logger.info(
            "reranker_completed "
            "model=%s model_was_warm=%s "
            "candidate_count=%s "
            "returned_count=%s "
            "batch_size=%s "
            "predict_ms=%.3f "
            "total_ms=%.3f",
            settings
            .retrieval_reranker_model_name,
            model_was_warm,
            len(candidates),
            len(results),
            settings
            .retrieval_reranker_batch_size,
            predict_ms,
            total_ms,
        )

        return results
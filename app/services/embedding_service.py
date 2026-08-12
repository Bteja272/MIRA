import logging
from time import perf_counter

from sentence_transformers import SentenceTransformer

from app.core.config import settings


logger = logging.getLogger(__name__)


class EmbeddingService:
    _model = None

    @classmethod
    def is_model_loaded(cls) -> bool:
        return cls._model is not None

    @classmethod
    def get_model(cls) -> SentenceTransformer:
        if cls._model is None:
            started_at = perf_counter()

            cls._model = SentenceTransformer(
                settings.embedding_model_name
            )

            logger.info(
                "embedding_model_loaded "
                "model=%s load_ms=%.3f",
                settings.embedding_model_name,
                (
                    perf_counter()
                    - started_at
                )
                * 1000,
            )

        return cls._model

    @classmethod
    def embed_text(
        cls,
        text: str,
    ) -> list[float]:
        model_was_warm = (
            cls._model is not None
        )
        started_at = perf_counter()

        model = cls.get_model()

        encode_started_at = (
            perf_counter()
        )
        embedding = model.encode(
            text,
            convert_to_numpy=True,
        )
        encode_ms = (
            perf_counter()
            - encode_started_at
        ) * 1000
        total_ms = (
            perf_counter()
            - started_at
        ) * 1000

        logger.info(
            "embedding_text_completed "
            "model=%s model_was_warm=%s "
            "characters=%s encode_ms=%.3f "
            "total_ms=%.3f",
            settings.embedding_model_name,
            model_was_warm,
            len(text),
            encode_ms,
            total_ms,
        )

        return embedding.tolist()

    @classmethod
    def embed_texts(
        cls,
        texts: list[str],
    ) -> list[list[float]]:
        model_was_warm = (
            cls._model is not None
        )
        started_at = perf_counter()

        model = cls.get_model()

        encode_started_at = (
            perf_counter()
        )
        embeddings = model.encode(
            texts,
            convert_to_numpy=True,
        )
        encode_ms = (
            perf_counter()
            - encode_started_at
        ) * 1000
        total_ms = (
            perf_counter()
            - started_at
        ) * 1000

        logger.info(
            "embedding_batch_completed "
            "model=%s model_was_warm=%s "
            "text_count=%s characters=%s "
            "encode_ms=%.3f total_ms=%.3f",
            settings.embedding_model_name,
            model_was_warm,
            len(texts),
            sum(len(text) for text in texts),
            encode_ms,
            total_ms,
        )

        return [
            embedding.tolist()
            for embedding in embeddings
        ]
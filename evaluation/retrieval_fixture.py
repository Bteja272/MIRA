from __future__ import annotations

from sqlalchemy import select

from app.db.models import (
    Document,
    DocumentChunk,
    User,
)
from app.db.session import SessionLocal
from app.services.embedding_service import (
    EmbeddingService,
)
from evaluation.corpus_loader import (
    EvaluationCorpus,
)


class RetrievalEvaluationFixture:
    @staticmethod
    def reset(
        corpus: EvaluationCorpus,
    ) -> None:
        user_id = corpus.evaluation_user[
            "user_id"
        ]
        email = corpus.evaluation_user[
            "email"
        ]

        db = SessionLocal()

        try:
            existing_documents = list(
                db.scalars(
                    select(Document)
                    .where(
                        Document.user_id
                        == user_id
                    )
                )
            )

            for document in (
                existing_documents
            ):
                db.delete(document)

            existing_user = db.scalar(
                select(User)
                .where(
                    User.user_id
                    == user_id
                )
            )

            if existing_user is not None:
                db.delete(
                    existing_user
                )

            db.flush()

            user = User(
                user_id=user_id,
                email=email,
                password_hash=(
                    "evaluation-only-"
                    "not-for-login"
                ),
                is_active=True,
            )

            db.add(user)
            db.flush()

            all_chunks: list[
                tuple[
                    dict,
                    dict,
                ]
            ] = []

            for document_payload in (
                corpus.documents
            ):
                document = Document(
                    document_id=(
                        document_payload[
                            "document_id"
                        ]
                    ),
                    user_id=user_id,
                    source=(
                        document_payload[
                            "filename"
                        ]
                    ),
                    original_filename=(
                        document_payload[
                            "filename"
                        ]
                    ),
                    stored_filename=(
                        document_payload[
                            "filename"
                        ]
                    ),
                    document_type=(
                        document_payload[
                            "document_type"
                        ]
                    ),
                    file_hash=None,
                    file_size_bytes=None,
                )

                db.add(document)

                for chunk_payload in (
                    document_payload[
                        "chunks"
                    ]
                ):
                    all_chunks.append(
                        (
                            document_payload,
                            chunk_payload,
                        )
                    )

            db.flush()

            texts = [
                chunk_payload[
                    "text"
                ]
                for (
                    _document_payload,
                    chunk_payload,
                )
                in all_chunks
            ]

            embeddings = (
                EmbeddingService
                .embed_texts(
                    texts
                )
            )

            for (
                (
                    document_payload,
                    chunk_payload,
                ),
                embedding,
            ) in zip(
                all_chunks,
                embeddings,
                strict=True,
            ):
                db.add(
                    DocumentChunk(
                        chunk_id=(
                            chunk_payload[
                                "chunk_id"
                            ]
                        ),
                        document_id=(
                            document_payload[
                                "document_id"
                            ]
                        ),
                        page_number=(
                            chunk_payload.get(
                                "page_number"
                            )
                        ),
                        chunk_index=(
                            chunk_payload[
                                "chunk_index"
                            ]
                        ),
                        text=(
                            chunk_payload[
                                "text"
                            ]
                        ),
                        embedding=embedding,
                    )
                )

            db.commit()

        except Exception:
            db.rollback()
            raise

        finally:
            db.close()

    @staticmethod
    def cleanup(
        corpus: EvaluationCorpus,
    ) -> None:
        user_id = corpus.evaluation_user[
            "user_id"
        ]

        db = SessionLocal()

        try:
            documents = list(
                db.scalars(
                    select(Document)
                    .where(
                        Document.user_id
                        == user_id
                    )
                )
            )

            for document in documents:
                db.delete(document)

            user = db.scalar(
                select(User)
                .where(
                    User.user_id
                    == user_id
                )
            )

            if user is not None:
                db.delete(user)

            db.commit()

        except Exception:
            db.rollback()
            raise

        finally:
            db.close()
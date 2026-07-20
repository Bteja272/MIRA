from langchain_core.documents import (
    Document as LangChainDocument,
)

from app.services.retrieval_service import (
    RetrievalService,
)


class LangChainRetrieverService:
    @staticmethod
    def _to_langchain_document(
        result: dict,
    ) -> LangChainDocument:
        return LangChainDocument(
            page_content=result["text"],
            metadata={
                "chunk_id": (
                    result["chunk_id"]
                ),
                "document_id": (
                    result["document_id"]
                ),
                "source": (
                    result["source"]
                ),
                "document_type": (
                    result.get(
                        "document_type"
                    )
                ),
                "page_number": (
                    result.get(
                        "page_number"
                    )
                ),
                "chunk_index": (
                    result["chunk_index"]
                ),
                "similarity_score": (
                    result.get(
                        "similarity_score"
                    )
                ),
                "document_position": (
                    result.get(
                        "document_position"
                    )
                ),
            },
        )

    @classmethod
    def retrieve(
        cls,
        query: str,
        top_k: int,
        document_id: str | None = None,
        document_ids: list[str] | None = None,
        user_id: str | None = None,
    ) -> list[LangChainDocument]:
        results = (
            RetrievalService.retrieve(
                query=query,
                top_k=top_k,
                document_id=document_id,
                document_ids=document_ids,
                user_id=user_id,
            )
        )

        return [
            cls._to_langchain_document(
                result
            )
            for result in results
        ]

    @classmethod
    def retrieve_document(
        cls,
        document_id: str,
        user_id: str | None = None,
    ) -> list[LangChainDocument]:
        results = (
            RetrievalService
            .retrieve_document(
                document_id=document_id,
                user_id=user_id,
                document_position=1,
            )
        )

        return [
            cls._to_langchain_document(
                result
            )
            for result in results
        ]

    @classmethod
    def retrieve_documents(
        cls,
        document_ids: list[str],
        user_id: str | None = None,
    ) -> list[LangChainDocument]:
        results = (
            RetrievalService
            .retrieve_documents(
                document_ids=document_ids,
                user_id=user_id,
            )
        )

        return [
            cls._to_langchain_document(
                result
            )
            for result in results
        ]

    @staticmethod
    def get_latest_document_id(
        user_id: str | None = None,
    ) -> str | None:
        return (
            RetrievalService
            .get_latest_document_id(
                user_id=user_id
            )
        )

    @staticmethod
    def to_source_dicts(
        documents: list[
            LangChainDocument
        ],
    ) -> list[dict]:
        sources: list[dict] = []

        for (
            source_number,
            document,
        ) in enumerate(
            documents,
            start=1,
        ):
            metadata = (
                document.metadata or {}
            )

            sources.append(
                {
                    "source_number": (
                        source_number
                    ),
                    "chunk_id": (
                        metadata.get(
                            "chunk_id"
                        )
                    ),
                    "document_id": (
                        metadata.get(
                            "document_id"
                        )
                    ),
                    "source": (
                        metadata.get(
                            "source"
                        )
                    ),
                    "document_type": (
                        metadata.get(
                            "document_type"
                        )
                    ),
                    "document_position": (
                        metadata.get(
                            "document_position"
                        )
                    ),
                    "page_number": (
                        metadata.get(
                            "page_number"
                        )
                    ),
                    "chunk_index": (
                        metadata.get(
                            "chunk_index"
                        )
                    ),
                    "similarity_score": (
                        metadata.get(
                            "similarity_score"
                        )
                    ),
                    "text": (
                        document.page_content
                    ),
                }
            )

        return sources
from langchain_core.documents import Document

from app.services.retrieval_service import RetrievalService


class LangChainRetrieverService:
    @staticmethod
    def _to_documents(chunks: list[dict]) -> list[Document]:
        return [
            Document(
                page_content=chunk["text"],
                metadata={
                    "chunk_id": chunk["chunk_id"],
                    "document_id": chunk["document_id"],
                    "source": chunk.get("source"),
                    "page_number": chunk["page_number"],
                    "chunk_index": chunk["chunk_index"],
                    "similarity_score": chunk.get(
                        "similarity_score"
                    ),
                },
            )
            for chunk in chunks
        ]

    @staticmethod
    def retrieve(
        query: str,
        top_k: int = 3,
        document_id: str | None = None,
    ) -> list[Document]:
        chunks = RetrievalService.retrieve(
            query=query,
            top_k=top_k,
            document_id=document_id,
        )

        return LangChainRetrieverService._to_documents(chunks)

    @staticmethod
    def retrieve_document(
        document_id: str,
    ) -> list[Document]:
        chunks = RetrievalService.retrieve_document(document_id)

        return LangChainRetrieverService._to_documents(chunks)

    @staticmethod
    def get_latest_document_id() -> str | None:
        return RetrievalService.get_latest_document_id()

    @staticmethod
    def to_source_dicts(
        documents: list[Document],
    ) -> list[dict]:
        return [
            {
                "chunk_id": document.metadata.get("chunk_id"),
                "document_id": document.metadata.get(
                    "document_id"
                ),
                "source": document.metadata.get("source"),
                "page_number": document.metadata.get(
                    "page_number"
                ),
                "chunk_index": document.metadata.get(
                    "chunk_index"
                ),
                "similarity_score": document.metadata.get(
                    "similarity_score"
                ),
                "text": document.page_content,
            }
            for document in documents
        ]
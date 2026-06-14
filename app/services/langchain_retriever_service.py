from langchain_core.documents import Document

from app.services.retrieval_service import RetrievalService


class LangChainRetrieverService:
    @staticmethod
    def retrieve(query: str, top_k: int = 3) -> list[Document]:
        chunks = RetrievalService.retrieve(
            query=query,
            top_k=top_k,
        )

        return [
            Document(
                page_content=chunk["text"],
                metadata={
                    "chunk_id": chunk["chunk_id"],
                    "document_id": chunk["document_id"],
                    "page_number": chunk["page_number"],
                    "chunk_index": chunk["chunk_index"],
                },
            )
            for chunk in chunks
        ]

    @staticmethod
    def to_source_dicts(documents: list[Document]) -> list[dict]:
        return [
            {
                "chunk_id": document.metadata.get("chunk_id"),
                "document_id": document.metadata.get("document_id"),
                "page_number": document.metadata.get("page_number"),
                "chunk_index": document.metadata.get("chunk_index"),
                "text": document.page_content,
            }
            for document in documents
        ]
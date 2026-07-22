import re
import time

from app.core.config import settings
from app.services.document_merge_service import (
    DocumentMergeService,
)
from app.services.document_service import (
    DocumentService,
)
from app.services.langchain_retriever_service import (
    LangChainRetrieverService,
)
from app.services.llm_service import (
    LLMService,
)
from app.services.medical_prompt_service import (
    MedicalPromptService,
)
from app.services.prompt_service import (
    PromptService,
)
from app.services.response_validation_service import (
    ResponseValidationService,
)


class RAGService:
    SUMMARY_KEYWORDS = (
        "summarize",
        "summarise",
        "summary",
        "overview",
        "give me an overview",
        "provide an overview",
        "what does this document say",
        "what is in this document",
    )

    COMPARISON_KEYWORDS = (
        "compare",
        "comparison",
        "difference",
        "differences",
        "changed",
        "changes",
        "trend",
        "trends",
        "over time",
        "between these",
        "across these",
        "earlier",
        "later",
    )

    DOCUMENT_IDENTIFICATION_QUERIES = {
        "what are the selected documents",
        "what are the two selected documents",
        "which documents are selected",
        "which files are selected",
        "what documents did i select",
        "what files did i select",
        "list selected documents",
        "list the selected documents",
        "what are the documents uploaded",
        "what are the two documents uploaded",
        "which documents were uploaded",
        "which files were uploaded",
        "list uploaded documents",
        "list the uploaded documents",
    }

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
                selected.append(
                    cleaned
                )

        return selected

    @staticmethod
    def _normalize_query_text(
        query: str,
    ) -> str:
        normalized = re.sub(
            r"[^a-z0-9\s]",
            " ",
            query.lower(),
        )

        return " ".join(
            normalized.split()
        )

    @classmethod
    def _is_document_identification_query(
        cls,
        query: str,
    ) -> bool:
        normalized_query = (
            cls._normalize_query_text(
                query
            )
        )

        return (
            normalized_query
            in cls
            .DOCUMENT_IDENTIFICATION_QUERIES
        )

    @classmethod
    def _is_summary_query(
        cls,
        query: str,
    ) -> bool:
        normalized_query = (
            query.lower().strip()
        )

        return any(
            keyword in normalized_query
            for keyword
            in cls.SUMMARY_KEYWORDS
        )

    @classmethod
    def _is_comparison_query(
        cls,
        query: str,
    ) -> bool:
        normalized_query = (
            query.lower().strip()
        )

        return any(
            keyword in normalized_query
            for keyword
            in cls.COMPARISON_KEYWORDS
        )

    @staticmethod
    def _format_document_type(
        document_type: str | None,
    ) -> str:
        if not document_type:
            return "Document"

        if document_type.lower() == "unknown":
            return "Document"

        return (
            document_type
            .replace("_", " ")
            .strip()
            .capitalize()
        )

    @classmethod
    def _document_identification_response(
        cls,
        query: str,
        selected_ids: list[str],
        started_at: float,
        user_id: str | None,
    ) -> dict:
        document_records: list[dict] = []

        for (
            document_position,
            selected_id,
        ) in enumerate(
            selected_ids,
            start=1,
        ):
            document = (
                DocumentService
                .get_document(
                    document_id=(
                        selected_id
                    ),
                    user_id=user_id,
                )
            )

            if document is None:
                continue

            document_records.append(
                {
                    **document,
                    "document_position": (
                        document_position
                    ),
                }
            )

        selected_document_id = (
            selected_ids[0]
            if len(selected_ids) == 1
            else None
        )

        if not document_records:
            answer = (
                "No selected documents "
                "were found."
            )

            return {
                "query": query,
                "answer": answer,
                "document_id": (
                    selected_document_id
                ),
                "document_ids": (
                    selected_ids
                ),
                "selected_document_count": (
                    len(selected_ids)
                ),
                "sources": [],
                "latency_seconds": round(
                    time.perf_counter()
                    - started_at,
                    3,
                ),
            }

        heading = (
            "The selected document is:"
            if len(document_records) == 1
            else (
                "The selected documents "
                "are:"
            )
        )

        answer_lines = [
            heading,
            "",
        ]

        sources: list[dict] = []

        for (
            source_number,
            document,
        ) in enumerate(
            document_records,
            start=1,
        ):
            filename = document.get(
                "filename"
            ) or "Unknown filename"

            formatted_type = (
                cls._format_document_type(
                    document.get(
                        "document_type"
                    )
                )
            )

            answer_lines.append(
                (
                    f"{source_number}. "
                    f"{filename} — "
                    f"{formatted_type}"
                )
            )

            sources.append(
                {
                    "source_number": (
                        source_number
                    ),
                    "chunk_id": None,
                    "document_id": (
                        document.get(
                            "document_id"
                        )
                    ),
                    "source": filename,
                    "document_type": (
                        document.get(
                            "document_type"
                        )
                    ),
                    "document_position": (
                        document.get(
                            "document_position"
                        )
                    ),
                    "page_number": None,
                    "chunk_index": None,
                    "similarity_score": None,
                    "text": None,
                }
            )

        return {
            "query": query,
            "answer": "\n".join(
                answer_lines
            ).strip(),
            "document_id": (
                selected_document_id
            ),
            "document_ids": selected_ids,
            "selected_document_count": (
                len(selected_ids)
            ),
            "sources": sources,
            "latency_seconds": round(
                time.perf_counter()
                - started_at,
                3,
            ),
        }

    @classmethod
    def query(
        cls,
        query: str,
        document_id: str | None = None,
        document_ids: list[str] | None = None,
        user_id: str | None = None,
    ) -> dict:
        started_at = (
            time.perf_counter()
        )

        selected_ids = (
            cls._normalize_document_ids(
                document_id=document_id,
                document_ids=document_ids,
            )
        )

        if (
            selected_ids
            and cls
            ._is_document_identification_query(
                query
            )
        ):
            return (
                cls
                ._document_identification_response(
                    query=query,
                    selected_ids=(
                        selected_ids
                    ),
                    started_at=(
                        started_at
                    ),
                    user_id=user_id,
                )
            )

        is_summary = (
            cls._is_summary_query(
                query
            )
        )

        is_comparison = (
            cls._is_comparison_query(
                query
            )
        )

        if (
            not selected_ids
            and is_summary
        ):
            latest_document_id = (
                LangChainRetrieverService
                .get_latest_document_id(
                    user_id=user_id,
                )
            )

            if latest_document_id:
                selected_ids = [
                    latest_document_id
                ]

        if len(selected_ids) > 1:
            retrieved_documents = (
                LangChainRetrieverService
                .retrieve_documents(
                    document_ids=(
                        selected_ids
                    ),
                    user_id=user_id,
                )
            )

            task = (
                "comparison"
                if is_comparison
                else (
                    "multi_document_"
                    "overview"
                )
            )

        elif (
            len(selected_ids) == 1
            and is_summary
        ):
            retrieved_documents = (
                LangChainRetrieverService
                .retrieve_document(
                    document_id=(
                        selected_ids[0]
                    ),
                    user_id=user_id,
                )
            )

            task = "summarization"

        else:
            retrieved_documents = (
                LangChainRetrieverService
                .retrieve(
                    query=query,
                    top_k=(
                        settings
                        .retrieval_top_k
                    ),
                    document_ids=(
                        selected_ids or None
                    ),
                    user_id=user_id,
                )
            )

            task = "qa"

        selected_document_id = (
            selected_ids[0]
            if len(selected_ids) == 1
            else None
        )

        if not retrieved_documents:
            answer = (
                "I could not find relevant "
                "information in the selected "
                "uploaded document or documents."
            )

            answer = (
                MedicalPromptService
                .ensure_disclaimer(
                    answer
                )
            )

            return {
                "query": query,
                "answer": answer,
                "document_id": (
                    selected_document_id
                ),
                "document_ids": (
                    selected_ids
                ),
                "selected_document_count": (
                    len(selected_ids)
                ),
                "sources": [],
                "latency_seconds": round(
                    time.perf_counter()
                    - started_at,
                    3,
                ),
            }

        prompt_documents = (
            DocumentMergeService
            .merge_documents(
                retrieved_documents
            )
        )

        prompt = (
            PromptService.build_prompt(
                query=query,
                documents=(
                    prompt_documents
                ),
                task=task,
            )
        )

        answer = (
            LLMService.generate_response(
                prompt=prompt,
                system_prompt=(
                    MedicalPromptService
                    .document_system_prompt()
                ),
            )
        )

        answer = (
            ResponseValidationService
            .sanitize_document_answer(
                answer
            )
        )

        answer = (
            MedicalPromptService
            .ensure_disclaimer(
                answer
            )
        )

        # Sources now match the source numbers used in the prompt.
        # Each source represents one complete merged document.
        sources = (
            LangChainRetrieverService
            .to_source_dicts(
                prompt_documents
            )
        )

        return {
            "query": query,
            "answer": answer,
            "document_id": (
                selected_document_id
            ),
            "document_ids": selected_ids,
            "selected_document_count": (
                len(selected_ids)
            ),
            "sources": sources,
            "latency_seconds": round(
                time.perf_counter()
                - started_at,
                3,
            ),
        }
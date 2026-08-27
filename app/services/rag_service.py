import logging
import re
import time

from app.core.config import settings
from app.services.document_merge_service import (
    DocumentMergeService,
)
from app.services.document_service import (
    DocumentService,
)
from app.services.context_optimization_service import (
    ContextOptimizationService,
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
from app.services.conversation_memory_service import (
    ConversationMemoryService,
)


logger = logging.getLogger(__name__)


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

    BROAD_QA_TERMS = {
        "all",
        "list",
        "medications",
        "medicines",
        "labs",
        "laboratory",
        "results",
        "findings",
        "diagnoses",
        "procedures",
        "instructions",
        "everything",
    }

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
    def _elapsed_ms(
        started_at: float,
    ) -> float:
        return round(
            (
                time.perf_counter()
                - started_at
            )
            * 1000,
            3,
        )

    @staticmethod
    def _new_timings() -> dict[str, float]:
        return {
            "latest_document_lookup_ms": 0.0,
            "retrieval_ms": 0.0,
            "document_merge_ms": 0.0,
            "context_optimization_ms": 0.0,
            "prompt_build_ms": 0.0,
            "llm_generation_ms": 0.0,
            "response_validation_ms": 0.0,
            "response_repair_ms": 0.0,
            "response_revalidation_ms": 0.0,
            "response_fallback_ms": 0.0,
            "disclaimer_ms": 0.0,
            "source_build_ms": 0.0,
            "total_ms": 0.0,
        }

    @staticmethod
    def _log_completion(
        *,
        task: str,
        selected_document_count: int,
        retrieved_count: int,
        source_count: int,
        timings: dict[str, float],
    ) -> None:
        logger.info(
            "rag_query_completed "
            "task=%s selected_count=%s "
            "retrieved_count=%s "
            "source_count=%s timings=%s",
            task,
            selected_document_count,
            retrieved_count,
            source_count,
            timings,
        )

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

    @classmethod
    def _qa_top_k(
        cls,
        query: str,
    ) -> int:
        base_top_k = (
            settings.retrieval_top_k
        )

        if not (
            settings
            .retrieval_adaptive_top_k_enabled
        ):
            return base_top_k

        normalized_query = (
            cls._normalize_query_text(
                query
            )
        )

        query_terms = set(
            normalized_query.split()
        )

        is_broad_query = bool(
            query_terms
            & cls.BROAD_QA_TERMS
        )

        if not is_broad_query:
            return base_top_k

        return max(
            base_top_k,
            min(
                settings
                .retrieval_adaptive_top_k_max,
                settings
                .retrieval_candidate_k,
            ),
        )

    @staticmethod
    def _context_token_budget(
        task: str,
    ) -> int:
        if task == "qa":
            return (
                settings
                .rag_qa_context_max_estimated_tokens
            )

        if task == "summarization":
            return (
                settings
                .rag_summary_context_max_estimated_tokens
            )

        return (
            settings
            .rag_multi_document_context_max_estimated_tokens
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
        timings = cls._new_timings()
        document_records: list[dict] = []

        retrieval_started_at = (
            time.perf_counter()
        )

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

        timings["retrieval_ms"] = (
            cls._elapsed_ms(
                retrieval_started_at
            )
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

            timings["total_ms"] = (
                cls._elapsed_ms(
                    started_at
                )
            )

            cls._log_completion(
                task="document_identification",
                selected_document_count=(
                    len(selected_ids)
                ),
                retrieved_count=0,
                source_count=0,
                timings=timings,
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
                    (
                        time.perf_counter()
                        - started_at
                    ),
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

        source_started_at = (
            time.perf_counter()
        )
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

        timings["source_build_ms"] = (
            cls._elapsed_ms(
                source_started_at
            )
        )
        timings["total_ms"] = (
            cls._elapsed_ms(
                started_at
            )
        )

        cls._log_completion(
            task="document_identification",
            selected_document_count=(
                len(selected_ids)
            ),
            retrieved_count=(
                len(document_records)
            ),
            source_count=len(sources),
            timings=timings,
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
                (
                    time.perf_counter()
                    - started_at
                ),
                3,
            ),
        }


    @classmethod
    def _build_source_grounded_fallback(
        cls,
        documents: list,
    ) -> str:
        """
        Build a deterministic extractive fallback from the exact
        optimized source context supplied to the LLM.

        Every retained source sentence is copied verbatim and receives
        the source label for the document it came from. No new medical
        facts, calculations, interpretations, or source labels are
        generated.
        """
        sections: list[str] = []

        for source_number, document in enumerate(
            documents,
            start=1,
        ):
            metadata = getattr(
                document,
                "metadata",
                {},
            ) or {}

            source_name = str(
                metadata.get(
                    "source",
                    f"Source {source_number}",
                )
            )

            cited_sentences: list[str] = []

            for raw_line in str(
                document.page_content or ""
            ).splitlines():
                line = raw_line.strip()

                if not line:
                    continue

                # Keep sentence boundaries so each factual sentence has
                # its own deterministic citation.
                sentence_parts = re.split(
                    r"(?<=[.!?])\s+",
                    line,
                )

                for sentence in sentence_parts:
                    cleaned = sentence.strip()

                    if not cleaned:
                        continue

                    terminal = ""
                    sentence_body = cleaned

                    if cleaned[-1:] in {
                        ".",
                        "!",
                        "?",
                    }:
                        terminal = cleaned[-1]
                        sentence_body = (
                            cleaned[:-1]
                            .rstrip()
                        )

                    cited_sentences.append(
                        f"{sentence_body} "
                        f"[Source {source_number}]"
                        f"{terminal}"
                    )

            if not cited_sentences:
                continue

            sections.append(
                "\n".join(
                    [
                        f"Document: {source_name}",
                        *cited_sentences,
                    ]
                )
            )

        if not sections:
            return (
                "I could not find source-grounded information in the "
                "selected document context."
            )

        return (
            "I could not safely preserve the generated answer, so the "
            "relevant source-grounded document text is shown below.\n\n"
            + "\n\n".join(
                sections
            )
        )

    @classmethod
    def query(
        cls,
        query: str,
        document_id: str | None = None,
        document_ids: list[str] | None = None,
        user_id: str | None = None,
        conversation_context: (
            list[dict[str, str]]
            | None
        ) = None,
        retrieval_query: str | None = None,
    ) -> dict:
        started_at = (
            time.perf_counter()
        )
        timings = cls._new_timings()

        effective_retrieval_query = (
            retrieval_query or query
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
            lookup_started_at = (
                time.perf_counter()
            )
            latest_document_id = (
                LangChainRetrieverService
                .get_latest_document_id(
                    user_id=user_id,
                )
            )
            timings[
                "latest_document_lookup_ms"
            ] = cls._elapsed_ms(
                lookup_started_at
            )

            if latest_document_id:
                selected_ids = [
                    latest_document_id
                ]

        retrieval_started_at = (
            time.perf_counter()
        )

        retrieval_top_k_used: (
            int | None
        ) = None

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
            retrieval_top_k_used = (
                cls._qa_top_k(
                    query
                )
            )

            retrieved_documents = (
                LangChainRetrieverService
                .retrieve(
                    query=(
                        effective_retrieval_query
                    ),
                    top_k=(
                        retrieval_top_k_used
                    ),
                    document_ids=(
                        selected_ids or None
                    ),
                    user_id=user_id,
                )
            )

            task = "qa"

        timings["retrieval_ms"] = (
            cls._elapsed_ms(
                retrieval_started_at
            )
        )

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

            disclaimer_started_at = (
                time.perf_counter()
            )
            answer = (
                MedicalPromptService
                .ensure_disclaimer(
                    answer
                )
            )
            timings["disclaimer_ms"] = (
                cls._elapsed_ms(
                    disclaimer_started_at
                )
            )
            timings["total_ms"] = (
                cls._elapsed_ms(
                    started_at
                )
            )

            cls._log_completion(
                task=task,
                selected_document_count=(
                    len(selected_ids)
                ),
                retrieved_count=0,
                source_count=0,
                timings=timings,
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
                    (
                        time.perf_counter()
                        - started_at
                    ),
                    3,
                ),
            }

        merge_started_at = (
            time.perf_counter()
        )
        prompt_documents = (
            DocumentMergeService
            .merge_documents(
                retrieved_documents
            )
        )
        timings["document_merge_ms"] = (
            cls._elapsed_ms(
                merge_started_at
            )
        )

        context_started_at = (
            time.perf_counter()
        )

        context_result = (
            ContextOptimizationService
            .optimize(
                documents=(
                    prompt_documents
                ),
                token_budget=(
                    cls
                    ._context_token_budget(
                        task
                    )
                ),
            )
        )

        prompt_documents = (
            context_result.documents
        )

        timings[
            "context_optimization_ms"
        ] = cls._elapsed_ms(
            context_started_at
        )

        prompt_started_at = (
            time.perf_counter()
        )
        prompt_query = (
            ConversationMemoryService
            .build_prompt_query(
                query=query,
                context=(
                    conversation_context
                ),
            )
        )
        prompt = (
            PromptService.build_prompt(
                query=prompt_query,
                documents=(
                    prompt_documents
                ),
                task=task,
            )
        )
        timings["prompt_build_ms"] = (
            cls._elapsed_ms(
                prompt_started_at
            )
        )

        context_metrics = (
            context_result.metrics
        )

        logger.info(
            "rag_context_prepared "
            "task=%s retrieval_top_k=%s "
            "input_document_count=%s "
            "output_document_count=%s "
            "input_characters=%s "
            "output_characters=%s "
            "input_estimated_tokens=%s "
            "output_estimated_tokens=%s "
            "token_budget=%s "
            "truncated_document_count=%s "
            "prompt_characters=%s "
            "context_optimization_ms=%.3f",
            task,
            (
                retrieval_top_k_used
                if retrieval_top_k_used
                is not None
                else "full_document"
            ),
            context_metrics
            .input_document_count,
            context_metrics
            .output_document_count,
            context_metrics
            .input_characters,
            context_metrics
            .output_characters,
            context_metrics
            .input_estimated_tokens,
            context_metrics
            .output_estimated_tokens,
            context_metrics
            .token_budget,
            context_metrics
            .truncated_document_count,
            len(prompt),
            timings[
                "context_optimization_ms"
            ],
        )

        # Build source dictionaries before post-generation validation so
        # citation labels can be checked against the exact numbered
        # prompt context.
        source_started_at = (
            time.perf_counter()
        )
        sources = (
            LangChainRetrieverService
            .to_source_dicts(
                prompt_documents
            )
        )

        # Ensure validation always has the same source text that the LLM
        # saw even if the public source serializer omits chunk text.
        for index, (
            source,
            document,
        ) in enumerate(
            zip(
                sources,
                prompt_documents,
                strict=False,
            ),
            start=1,
        ):
            source.setdefault(
                "source_number",
                index,
            )

            if not source.get(
                "text"
            ):
                source["text"] = (
                    document.page_content
                )

        timings["source_build_ms"] = (
            cls._elapsed_ms(
                source_started_at
            )
        )

        llm_started_at = (
            time.perf_counter()
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
        timings["llm_generation_ms"] = (
            cls._elapsed_ms(
                llm_started_at
            )
        )

        validation_started_at = (
            time.perf_counter()
        )
        answer = (
            ResponseValidationService
            .sanitize_document_answer(
                answer
            )
        )

        validation = (
            ResponseValidationService
            .validate_grounded_answer(
                answer=answer,
                sources=sources,
            )
        )

        timings[
            "response_validation_ms"
        ] = cls._elapsed_ms(
            validation_started_at
        )

        if not validation.is_valid:
            logger.warning(
                "rag_response_validation_failed "
                "task=%s issues=%s "
                "unsupported_value_count=%s "
                "invalid_citation_count=%s "
                "uncited_value_count=%s "
                "misattributed_value_count=%s",
                task,
                validation.issues,
                len(
                    validation
                    .unsupported_medical_values
                ),
                len(
                    validation
                    .invalid_citation_numbers
                ),
                len(
                    validation
                    .uncited_medical_values
                ),
                len(
                    validation
                    .misattributed_medical_values
                ),
            )

            # -------------------------------------------------
            # First recovery attempt:
            # constrained LLM repair
            # -------------------------------------------------

            repair_started_at = (
                time.perf_counter()
            )

            repair_prompt = (
                PromptService
                .build_repair_prompt(
                    query=prompt_query,
                    documents=(
                        prompt_documents
                    ),
                    answer=answer,
                    validation_issues=list(
                        validation.issues
                    ),
                )
            )

            repaired_answer = (
                LLMService
                .generate_response(
                    prompt=repair_prompt,
                    system_prompt=(
                        MedicalPromptService
                        .document_repair_system_prompt()
                    ),
                )
            )

            repaired_answer = (
                ResponseValidationService
                .sanitize_document_answer(
                    repaired_answer
                )
            )

            timings[
                "response_repair_ms"
            ] = cls._elapsed_ms(
                repair_started_at
            )

            # -------------------------------------------------
            # Revalidate repaired answer
            # -------------------------------------------------

            revalidation_started_at = (
                time.perf_counter()
            )

            repair_validation = (
                ResponseValidationService
                .validate_grounded_answer(
                    answer=repaired_answer,
                    sources=sources,
                )
            )

            timings[
                "response_revalidation_ms"
            ] = cls._elapsed_ms(
                revalidation_started_at
            )

            if repair_validation.is_valid:
                answer = repaired_answer

            else:
                logger.warning(
                    "rag_response_repair_failed "
                    "task=%s issues=%s "
                    "unsupported_value_count=%s "
                    "invalid_citation_count=%s "
                    "uncited_value_count=%s "
                    "misattributed_value_count=%s",
                    task,
                    repair_validation.issues,
                    len(
                        repair_validation
                        .unsupported_medical_values
                    ),
                    len(
                        repair_validation
                        .invalid_citation_numbers
                    ),
                    len(
                        repair_validation
                        .uncited_medical_values
                    ),
                    len(
                        repair_validation
                        .misattributed_medical_values
                    ),
                )

                # -------------------------------------------------
                # Final recovery:
                # deterministic source-grounded fallback
                # -------------------------------------------------

                fallback_started_at = (
                    time.perf_counter()
                )

                fallback_answer = (
                    cls
                    ._build_source_grounded_fallback(
                        prompt_documents
                    )
                )

                fallback_answer = (
                    ResponseValidationService
                    .sanitize_document_answer(
                        fallback_answer
                    )
                )

                fallback_validation = (
                    ResponseValidationService
                    .validate_grounded_answer(
                        answer=fallback_answer,
                        sources=sources,
                    )
                )

                timings[
                    "response_fallback_ms"
                ] = cls._elapsed_ms(
                    fallback_started_at
                )

                if fallback_validation.is_valid:
                    answer = fallback_answer

                else:
                    logger.error(
                        "rag_response_fallback_failed "
                        "task=%s issues=%s "
                        "unsupported_value_count=%s "
                        "invalid_citation_count=%s "
                        "uncited_value_count=%s "
                        "misattributed_value_count=%s",
                        task,
                        fallback_validation.issues,
                        len(
                            fallback_validation
                            .unsupported_medical_values
                        ),
                        len(
                            fallback_validation
                            .invalid_citation_numbers
                        ),
                        len(
                            fallback_validation
                            .uncited_medical_values
                        ),
                        len(
                            fallback_validation
                            .misattributed_medical_values
                        ),
                    )

                    answer = (
                        "I could not produce a fully "
                        "source-validated answer from "
                        "the selected document context. "
                        "Please review the source "
                        "material."
                    )

        disclaimer_started_at = (
            time.perf_counter()
        )
        answer = (
            MedicalPromptService
            .ensure_disclaimer(
                answer
            )
        )
        timings["disclaimer_ms"] = (
            cls._elapsed_ms(
                disclaimer_started_at
            )
        )

        timings["total_ms"] = (
            cls._elapsed_ms(
                started_at
            )
        )

        cls._log_completion(
            task=task,
            selected_document_count=(
                len(selected_ids)
            ),
            retrieved_count=(
                len(retrieved_documents)
            ),
            source_count=len(sources),
            timings=timings,
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
                (
                    time.perf_counter()
                    - started_at
                ),
                3,
            ),
        }
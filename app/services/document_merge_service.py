from collections import OrderedDict
from typing import Any

from langchain_core.documents import (
    Document as LangChainDocument,
)


class DocumentMergeService:
    """
    Merge retrieved chunks belonging to the same document.

    This prevents the language model from treating every chunk as a
    separate medical document and removes exact chunk overlap.
    """

    MINIMUM_OVERLAP_CHARACTERS = 20

    @staticmethod
    def _document_key(
        document: LangChainDocument,
        fallback_index: int,
    ) -> str:
        metadata = document.metadata or {}

        document_id = metadata.get(
            "document_id"
        )

        if document_id:
            return f"id:{document_id}"

        source = metadata.get(
            "source",
            "unknown",
        )

        document_position = metadata.get(
            "document_position",
            fallback_index,
        )

        return (
            f"source:{source}:"
            f"position:{document_position}"
        )

    @staticmethod
    def _chunk_sort_key(
        document: LangChainDocument,
    ) -> tuple[int, int]:
        metadata = document.metadata or {}

        page_number = metadata.get(
            "page_number"
        )

        chunk_index = metadata.get(
            "chunk_index"
        )

        page_value = (
            page_number
            if isinstance(page_number, int)
            else 0
        )

        chunk_value = (
            chunk_index
            if isinstance(chunk_index, int)
            else 0
        )

        return (
            page_value,
            chunk_value,
        )

    @classmethod
    def _merge_text_with_overlap(
        cls,
        existing_text: str,
        incoming_text: str,
    ) -> str:
        existing = (
            existing_text
            .replace("\r\n", "\n")
            .strip()
        )

        incoming = (
            incoming_text
            .replace("\r\n", "\n")
            .strip()
        )

        if not existing:
            return incoming

        if not incoming:
            return existing

        if incoming in existing:
            return existing

        if existing in incoming:
            return incoming

        maximum_overlap = min(
            len(existing),
            len(incoming),
        )

        for overlap_size in range(
            maximum_overlap,
            (
                cls
                .MINIMUM_OVERLAP_CHARACTERS
                - 1
            ),
            -1,
        ):
            if (
                existing[-overlap_size:]
                == incoming[:overlap_size]
            ):
                return (
                    existing
                    + incoming[
                        overlap_size:
                    ]
                )

        return (
            f"{existing}\n"
            f"{incoming}"
        )

    @staticmethod
    def _group_sort_key(
        group: dict[str, Any],
    ) -> tuple[int, int]:
        document_position = group.get(
            "document_position"
        )

        if isinstance(
            document_position,
            int,
        ):
            return (
                0,
                document_position,
            )

        return (
            1,
            group["first_seen_index"],
        )

    @classmethod
    def merge_documents(
        cls,
        documents: list[
            LangChainDocument
        ],
    ) -> list[
        LangChainDocument
    ]:
        if not documents:
            return []

        grouped_documents: OrderedDict[
            str,
            dict[str, Any],
        ] = OrderedDict()

        for index, document in enumerate(
            documents
        ):
            key = cls._document_key(
                document=document,
                fallback_index=index,
            )

            metadata = (
                document.metadata
                or {}
            )

            if key not in grouped_documents:
                grouped_documents[key] = {
                    "documents": [],
                    "first_seen_index": index,
                    "document_position": (
                        metadata.get(
                            "document_position"
                        )
                    ),
                }

            grouped_documents[
                key
            ]["documents"].append(
                document
            )

        ordered_groups = sorted(
            grouped_documents.values(),
            key=cls._group_sort_key,
        )

        merged_documents: list[
            LangChainDocument
        ] = []

        for group in ordered_groups:
            chunks = sorted(
                group["documents"],
                key=cls._chunk_sort_key,
            )

            merged_text = ""

            chunk_ids: list[str] = []
            chunk_indices: list[int] = []
            page_numbers: list[int] = []

            for chunk in chunks:
                merged_text = (
                    cls
                    ._merge_text_with_overlap(
                        existing_text=(
                            merged_text
                        ),
                        incoming_text=(
                            chunk.page_content
                        ),
                    )
                )

                chunk_metadata = (
                    chunk.metadata
                    or {}
                )

                chunk_id = (
                    chunk_metadata.get(
                        "chunk_id"
                    )
                )

                if chunk_id:
                    chunk_ids.append(
                        chunk_id
                    )

                chunk_index = (
                    chunk_metadata.get(
                        "chunk_index"
                    )
                )

                if isinstance(
                    chunk_index,
                    int,
                ):
                    chunk_indices.append(
                        chunk_index
                    )

                page_number = (
                    chunk_metadata.get(
                        "page_number"
                    )
                )

                if isinstance(
                    page_number,
                    int,
                ):
                    page_numbers.append(
                        page_number
                    )

            merged_metadata = dict(
                chunks[0].metadata or {}
            )

            merged_metadata.update(
                {
                    "chunk_id": None,
                    "chunk_ids": (
                        chunk_ids
                    ),
                    "chunk_index": None,
                    "chunk_indices": (
                        chunk_indices
                    ),
                    "merged_chunk_count": (
                        len(chunks)
                    ),
                    "similarity_score": None,
                }
            )

            unique_page_numbers = sorted(
                set(page_numbers)
            )

            if (
                len(unique_page_numbers)
                == 1
            ):
                merged_metadata[
                    "page_number"
                ] = unique_page_numbers[0]

            elif len(
                unique_page_numbers
            ) > 1:
                merged_metadata[
                    "page_number"
                ] = None

                merged_metadata[
                    "page_numbers"
                ] = (
                    unique_page_numbers
                )

            merged_documents.append(
                LangChainDocument(
                    page_content=(
                        merged_text
                    ),
                    metadata=(
                        merged_metadata
                    ),
                )
            )

        return merged_documents
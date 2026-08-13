from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class RetrievalCase:
    case_id: str
    query: str
    document_ids: list[str]
    relevant_chunk_ids: list[str]


@dataclass(frozen=True)
class EvaluationCorpus:
    version: str
    description: str
    evaluation_user: dict[str, str]
    documents: list[dict[str, Any]]
    retrieval_cases: list[RetrievalCase]

    @classmethod
    def load(
        cls,
        path: str | Path,
    ) -> "EvaluationCorpus":
        corpus_path = Path(path)

        payload = json.loads(
            corpus_path.read_text(
                encoding="utf-8"
            )
        )

        documents = list(
            payload.get(
                "documents",
                [],
            )
        )

        cases = [
            RetrievalCase(
                case_id=str(
                    case["case_id"]
                ),
                query=str(
                    case["query"]
                ),
                document_ids=[
                    str(document_id)
                    for document_id
                    in case.get(
                        "document_ids",
                        [],
                    )
                ],
                relevant_chunk_ids=[
                    str(chunk_id)
                    for chunk_id
                    in case.get(
                        "relevant_chunk_ids",
                        [],
                    )
                ],
            )
            for case
            in payload.get(
                "retrieval_cases",
                [],
            )
        ]

        corpus = cls(
            version=str(
                payload.get(
                    "version",
                    "unknown",
                )
            ),
            description=str(
                payload.get(
                    "description",
                    "",
                )
            ),
            evaluation_user=dict(
                payload.get(
                    "evaluation_user",
                    {},
                )
            ),
            documents=documents,
            retrieval_cases=cases,
        )

        corpus.validate()

        return corpus

    def validate(self) -> None:
        user_id = (
            self.evaluation_user
            .get(
                "user_id",
                "",
            )
            .strip()
        )

        email = (
            self.evaluation_user
            .get(
                "email",
                "",
            )
            .strip()
        )

        if not user_id:
            raise ValueError(
                "evaluation_user.user_id "
                "is required."
            )

        if not email:
            raise ValueError(
                "evaluation_user.email "
                "is required."
            )

        document_ids: set[str] = set()
        chunk_ids: set[str] = set()

        chunks_by_document: dict[
            str,
            set[str],
        ] = {}

        for document in self.documents:
            document_id = str(
                document.get(
                    "document_id",
                    "",
                )
            ).strip()

            if not document_id:
                raise ValueError(
                    "Each evaluation document "
                    "requires document_id."
                )

            if document_id in document_ids:
                raise ValueError(
                    "Duplicate evaluation "
                    f"document_id: {document_id}"
                )

            document_ids.add(
                document_id
            )

            document_chunk_ids: set[
                str
            ] = set()

            chunks = list(
                document.get(
                    "chunks",
                    [],
                )
            )

            if not chunks:
                raise ValueError(
                    f"{document_id} requires "
                    "at least one chunk."
                )

            for chunk in chunks:
                chunk_id = str(
                    chunk.get(
                        "chunk_id",
                        "",
                    )
                ).strip()

                if not chunk_id:
                    raise ValueError(
                        f"{document_id} contains "
                        "a chunk without chunk_id."
                    )

                if chunk_id in chunk_ids:
                    raise ValueError(
                        "Duplicate evaluation "
                        f"chunk_id: {chunk_id}"
                    )

                text = str(
                    chunk.get(
                        "text",
                        "",
                    )
                ).strip()

                if not text:
                    raise ValueError(
                        f"{chunk_id} has empty text."
                    )

                chunk_ids.add(
                    chunk_id
                )
                document_chunk_ids.add(
                    chunk_id
                )

            chunks_by_document[
                document_id
            ] = document_chunk_ids

        case_ids: set[str] = set()

        for case in self.retrieval_cases:
            if not case.case_id:
                raise ValueError(
                    "Each retrieval case "
                    "requires case_id."
                )

            if case.case_id in case_ids:
                raise ValueError(
                    "Duplicate retrieval "
                    f"case_id: {case.case_id}"
                )

            case_ids.add(
                case.case_id
            )

            if not case.query.strip():
                raise ValueError(
                    f"{case.case_id} has "
                    "an empty query."
                )

            if not case.document_ids:
                raise ValueError(
                    f"{case.case_id} requires "
                    "document_ids."
                )

            if not case.relevant_chunk_ids:
                raise ValueError(
                    f"{case.case_id} requires "
                    "relevant_chunk_ids."
                )

            missing_documents = [
                document_id
                for document_id
                in case.document_ids
                if document_id
                not in document_ids
            ]

            if missing_documents:
                raise ValueError(
                    f"{case.case_id} references "
                    "unknown document IDs: "
                    f"{missing_documents}"
                )

            allowed_chunks: set[str] = (
                set()
            )

            for document_id in (
                case.document_ids
            ):
                allowed_chunks.update(
                    chunks_by_document[
                        document_id
                    ]
                )

            invalid_relevant = [
                chunk_id
                for chunk_id
                in case.relevant_chunk_ids
                if chunk_id
                not in allowed_chunks
            ]

            if invalid_relevant:
                raise ValueError(
                    f"{case.case_id} references "
                    "relevant chunks outside "
                    "its document scope: "
                    f"{invalid_relevant}"
                )
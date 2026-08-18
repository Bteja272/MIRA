from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from evaluation.corpus_loader import (
    EvaluationCorpus,
)


@dataclass(frozen=True)
class RequiredFact:
    text: str
    aliases: list[str]
    source_document_ids: list[str]


@dataclass(frozen=True)
class RAGCase:
    case_id: str
    query: str
    document_ids: list[str]
    required_facts: list[RequiredFact]


@dataclass(frozen=True)
class ExtractionCase:
    case_id: str
    document_id: str
    evaluated_categories: list[str]
    expected: dict[str, list[dict[str, list[str]]]]


@dataclass(frozen=True)
class QualityCorpus:
    version: str
    description: str
    rag_cases: list[RAGCase]
    extraction_cases: list[ExtractionCase]

    @classmethod
    def load(
        cls,
        path: str | Path,
        *,
        retrieval_corpus: EvaluationCorpus,
    ) -> "QualityCorpus":
        payload = json.loads(
            Path(path).read_text(
                encoding="utf-8"
            )
        )

        rag_cases = [
            RAGCase(
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
                required_facts=[
                    RequiredFact(
                        text=str(
                            fact["text"]
                        ),
                        aliases=[
                            str(alias)
                            for alias
                            in fact.get(
                                "aliases",
                                [],
                            )
                        ],
                        source_document_ids=[
                            str(document_id)
                            for document_id
                            in fact.get(
                                "source_document_ids",
                                [],
                            )
                        ],
                    )
                    for fact
                    in case.get(
                        "required_facts",
                        [],
                    )
                ],
            )
            for case
            in payload.get(
                "rag_cases",
                [],
            )
        ]

        extraction_cases = [
            ExtractionCase(
                case_id=str(
                    case["case_id"]
                ),
                document_id=str(
                    case["document_id"]
                ),
                evaluated_categories=[
                    str(category)
                    for category
                    in case.get(
                        "evaluated_categories",
                        [],
                    )
                ],
                expected={
                    str(category): [
                        {
                            str(field_name): [
                                str(value)
                                for value
                                in values
                            ]
                            for (
                                field_name,
                                values,
                            )
                            in item.items()
                        }
                        for item in items
                    ]
                    for category, items
                    in case.get(
                        "expected",
                        {},
                    ).items()
                },
            )
            for case
            in payload.get(
                "extraction_cases",
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
            rag_cases=rag_cases,
            extraction_cases=(
                extraction_cases
            ),
        )

        corpus.validate(
            retrieval_corpus=(
                retrieval_corpus
            )
        )

        return corpus

    def validate(
        self,
        *,
        retrieval_corpus: EvaluationCorpus,
    ) -> None:
        known_documents = {
            str(
                document["document_id"]
            )
            for document
            in retrieval_corpus.documents
        }

        case_ids: set[str] = set()

        for case in self.rag_cases:
            if not case.case_id:
                raise ValueError(
                    "RAG case_id is required."
                )

            if case.case_id in case_ids:
                raise ValueError(
                    "Duplicate quality case_id: "
                    f"{case.case_id}"
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

            missing_documents = [
                document_id
                for document_id
                in case.document_ids
                if document_id
                not in known_documents
            ]

            if missing_documents:
                raise ValueError(
                    f"{case.case_id} references "
                    "unknown documents: "
                    f"{missing_documents}"
                )

            if not case.required_facts:
                raise ValueError(
                    f"{case.case_id} requires "
                    "at least one required fact."
                )

            for fact in case.required_facts:
                aliases = (
                    fact.aliases
                    or [fact.text]
                )

                if not any(
                    alias.strip()
                    for alias in aliases
                ):
                    raise ValueError(
                        f"{case.case_id} contains "
                        "an empty required fact."
                    )

                invalid_sources = [
                    document_id
                    for document_id
                    in fact.source_document_ids
                    if document_id
                    not in case.document_ids
                ]

                if invalid_sources:
                    raise ValueError(
                        f"{case.case_id} fact "
                        "references sources outside "
                        "the selected documents: "
                        f"{invalid_sources}"
                    )

        allowed_categories = {
            "diagnoses",
            "medications",
            "lab_results",
            "procedures",
            "follow_up_instructions",
        }

        for case in self.extraction_cases:
            if not case.case_id:
                raise ValueError(
                    "Extraction case_id is required."
                )

            if case.case_id in case_ids:
                raise ValueError(
                    "Duplicate quality case_id: "
                    f"{case.case_id}"
                )

            case_ids.add(
                case.case_id
            )

            if (
                case.document_id
                not in known_documents
            ):
                raise ValueError(
                    f"{case.case_id} references "
                    "an unknown document."
                )

            if not case.evaluated_categories:
                raise ValueError(
                    f"{case.case_id} requires "
                    "evaluated_categories."
                )

            invalid_categories = [
                category
                for category
                in case.evaluated_categories
                if category
                not in allowed_categories
            ]

            if invalid_categories:
                raise ValueError(
                    f"{case.case_id} has "
                    "unsupported categories: "
                    f"{invalid_categories}"
                )

            for category in (
                case.evaluated_categories
            ):
                if category not in case.expected:
                    raise ValueError(
                        f"{case.case_id} is missing "
                        f"gold data for {category}."
                    )

                for item in (
                    case.expected[
                        category
                    ]
                ):
                    if not item:
                        raise ValueError(
                            f"{case.case_id} has "
                            "an empty expected item."
                        )

                    for values in item.values():
                        if not values:
                            raise ValueError(
                                f"{case.case_id} has "
                                "an expected field "
                                "without accepted values."
                            )
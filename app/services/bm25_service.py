import math
import re
from collections import Counter


class BM25Service:
    """
    Small in-process Okapi BM25 implementation for MIRA.

    The service intentionally has no external dependency because
    document-scoped retrieval operates over a bounded chunk corpus.
    """

    TOKEN_PATTERN = re.compile(
        r"[a-z0-9]+(?:[./_-][a-z0-9]+)*",
        re.IGNORECASE,
    )

    @classmethod
    def tokenize(
        cls,
        text: str,
    ) -> list[str]:
        return [
            token.lower()
            for token in cls.TOKEN_PATTERN.findall(
                text or ""
            )
        ]

    @classmethod
    def rank(
        cls,
        *,
        query: str,
        documents: list[str],
        top_k: int,
        k1: float = 1.5,
        b: float = 0.75,
    ) -> list[tuple[int, float]]:
        if top_k <= 0:
            return []

        if not documents:
            return []

        query_tokens = cls.tokenize(
            query
        )

        if not query_tokens:
            return []

        tokenized_documents = [
            cls.tokenize(document)
            for document in documents
        ]

        document_count = len(
            tokenized_documents
        )

        document_lengths = [
            len(tokens)
            for tokens in tokenized_documents
        ]

        total_terms = sum(
            document_lengths
        )

        if total_terms == 0:
            return []

        average_document_length = (
            total_terms / document_count
        )

        document_frequencies: Counter[
            str
        ] = Counter()

        query_terms = set(
            query_tokens
        )

        for tokens in tokenized_documents:
            present_terms = (
                set(tokens)
                & query_terms
            )

            for term in present_terms:
                document_frequencies[
                    term
                ] += 1

        query_term_frequencies = Counter(
            query_tokens
        )

        scored: list[
            tuple[int, float]
        ] = []

        for (
            document_index,
            tokens,
        ) in enumerate(
            tokenized_documents
        ):
            if not tokens:
                continue

            term_frequencies = Counter(
                tokens
            )
            document_length = len(
                tokens
            )
            score = 0.0

            for (
                term,
                query_frequency,
            ) in (
                query_term_frequencies
                .items()
            ):
                term_frequency = (
                    term_frequencies.get(
                        term,
                        0,
                    )
                )

                if term_frequency <= 0:
                    continue

                document_frequency = (
                    document_frequencies.get(
                        term,
                        0,
                    )
                )

                idf = math.log(
                    1.0
                    + (
                        document_count
                        - document_frequency
                        + 0.5
                    )
                    / (
                        document_frequency
                        + 0.5
                    )
                )

                length_normalization = (
                    1.0
                    - b
                    + b
                    * (
                        document_length
                        / average_document_length
                    )
                )

                denominator = (
                    term_frequency
                    + k1
                    * length_normalization
                )

                term_score = (
                    idf
                    * (
                        term_frequency
                        * (k1 + 1.0)
                    )
                    / denominator
                )

                score += (
                    term_score
                    * query_frequency
                )

            if score > 0:
                scored.append(
                    (
                        document_index,
                        score,
                    )
                )

        scored.sort(
            key=lambda item: (
                -item[1],
                item[0],
            )
        )

        return scored[:top_k]
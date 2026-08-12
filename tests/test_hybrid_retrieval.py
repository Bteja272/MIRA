import unittest
from unittest.mock import (
    patch,
)

from app.core.config import settings
from app.services.cross_encoder_reranker_service import (
    CrossEncoderRerankerService,
)
from app.services.retrieval_service import (
    RetrievalService,
)


def _candidate(
    chunk_id: str,
    *,
    similarity_score: float | None,
    lexical_score: float | None = None,
) -> dict:
    return {
        "chunk_id": chunk_id,
        "document_id": "doc-1",
        "source": "synthetic.txt",
        "document_type": "lab_report",
        "page_number": 1,
        "chunk_index": 0,
        "similarity_score": (
            similarity_score
        ),
        "document_position": 1,
        "text": f"Synthetic {chunk_id}",
        "semantic_rank": None,
        "lexical_rank": None,
        "lexical_score": lexical_score,
        "hybrid_score": None,
        "retrieval_method": "test",
    }


class HybridRetrievalTests(
    unittest.TestCase
):
    def test_rrf_rewards_candidate_found_by_both_retrievers(
        self,
    ) -> None:
        semantic = [
            _candidate(
                "semantic-only",
                similarity_score=0.95,
            ),
            _candidate(
                "both",
                similarity_score=0.90,
            ),
        ]

        lexical = [
            _candidate(
                "both",
                similarity_score=None,
                lexical_score=5.2,
            ),
            _candidate(
                "lexical-only",
                similarity_score=None,
                lexical_score=4.8,
            ),
        ]

        with (
            patch.object(
                settings,
                "retrieval_rrf_k",
                60,
            ),
            patch.object(
                settings,
                "retrieval_semantic_weight",
                1.0,
            ),
            patch.object(
                settings,
                "retrieval_lexical_weight",
                1.0,
            ),
        ):
            results = (
                RetrievalService
                ._fuse_candidates(
                    semantic_candidates=(
                        semantic
                    ),
                    lexical_candidates=(
                        lexical
                    ),
                    top_k=3,
                )
            )

        self.assertEqual(
            results[0]["chunk_id"],
            "both",
        )
        self.assertEqual(
            results[0]["semantic_rank"],
            2,
        )
        self.assertEqual(
            results[0]["lexical_rank"],
            1,
        )
        self.assertEqual(
            results[0][
                "retrieval_method"
            ],
            "hybrid",
        )

    @patch.object(
        CrossEncoderRerankerService,
        "rerank",
    )
    @patch.object(
        RetrievalService,
        "_fuse_candidates",
    )
    @patch.object(
        RetrievalService,
        "_retrieve_lexical_candidates",
    )
    @patch.object(
        RetrievalService,
        "_retrieve_semantic_candidates",
    )
    def test_retrieve_fuses_broad_pool_then_reranks_to_final_top_k(
        self,
        mock_semantic,
        mock_lexical,
        mock_fuse,
        mock_rerank,
    ) -> None:
        fused = [
            _candidate(
                f"chunk-{index}",
                similarity_score=0.8,
            )
            for index in range(10)
        ]

        reranked = fused[:3]

        mock_semantic.return_value = (
            fused
        )
        mock_lexical.return_value = []
        mock_fuse.return_value = fused
        mock_rerank.return_value = (
            reranked
        )

        with (
            patch.object(
                settings,
                "retrieval_candidate_k",
                10,
            ),
            patch.object(
                settings,
                "retrieval_reranker_enabled",
                True,
            ),
        ):
            results = (
                RetrievalService.retrieve(
                    query="HbA1c",
                    top_k=3,
                    document_ids=[
                        "doc-1",
                    ],
                    user_id="user-1",
                )
            )

        self.assertEqual(
            mock_semantic
            .call_args.kwargs[
                "candidate_k"
            ],
            10,
        )
        self.assertEqual(
            mock_lexical
            .call_args.kwargs[
                "candidate_k"
            ],
            10,
        )
        self.assertEqual(
            mock_fuse
            .call_args.kwargs[
                "top_k"
            ],
            10,
        )
        self.assertEqual(
            mock_rerank
            .call_args.kwargs[
                "top_k"
            ],
            3,
        )
        self.assertEqual(
            results,
            reranked,
        )

    @patch.object(
        CrossEncoderRerankerService,
        "rerank",
    )
    @patch.object(
        RetrievalService,
        "_fuse_candidates",
    )
    @patch.object(
        RetrievalService,
        "_retrieve_lexical_candidates",
    )
    @patch.object(
        RetrievalService,
        "_retrieve_semantic_candidates",
    )
    def test_reranker_failure_falls_back_to_rrf_order(
        self,
        mock_semantic,
        mock_lexical,
        mock_fuse,
        mock_rerank,
    ) -> None:
        fused = [
            {
                **_candidate(
                    f"chunk-{index}",
                    similarity_score=0.8,
                ),
                "hybrid_score": (
                    0.1 - index * 0.001
                ),
                "retrieval_method": (
                    "hybrid"
                ),
            }
            for index in range(5)
        ]

        mock_semantic.return_value = (
            fused
        )
        mock_lexical.return_value = []
        mock_fuse.return_value = fused
        mock_rerank.side_effect = (
            RuntimeError(
                "synthetic reranker failure"
            )
        )

        with (
            patch.object(
                settings,
                "retrieval_reranker_enabled",
                True,
            ),
            patch.object(
                settings,
                "retrieval_reranker_fail_open",
                True,
            ),
        ):
            results = (
                RetrievalService.retrieve(
                    query="metformin",
                    top_k=3,
                    document_ids=[
                        "doc-1",
                    ],
                    user_id="user-1",
                )
            )

        self.assertEqual(
            [
                result["chunk_id"]
                for result in results
            ],
            [
                "chunk-0",
                "chunk-1",
                "chunk-2",
            ],
        )

        self.assertTrue(
            all(
                result[
                    "rerank_score"
                ]
                is None
                for result in results
            )
        )

    @patch.object(
        CrossEncoderRerankerService,
        "rerank",
    )
    @patch.object(
        RetrievalService,
        "_fuse_candidates",
    )
    @patch.object(
        RetrievalService,
        "_retrieve_lexical_candidates",
    )
    @patch.object(
        RetrievalService,
        "_retrieve_semantic_candidates",
    )
    def test_disabled_reranker_uses_rrf_order(
        self,
        mock_semantic,
        mock_lexical,
        mock_fuse,
        mock_rerank,
    ) -> None:
        fused = [
            {
                **_candidate(
                    f"chunk-{index}",
                    similarity_score=0.8,
                ),
                "hybrid_score": (
                    0.1 - index * 0.001
                ),
            }
            for index in range(4)
        ]

        mock_semantic.return_value = (
            fused
        )
        mock_lexical.return_value = []
        mock_fuse.return_value = fused

        with patch.object(
            settings,
            "retrieval_reranker_enabled",
            False,
        ):
            results = (
                RetrievalService.retrieve(
                    query="LDL",
                    top_k=3,
                    document_ids=[
                        "doc-1",
                    ],
                    user_id="user-1",
                )
            )

        mock_rerank.assert_not_called()

        self.assertEqual(
            len(results),
            3,
        )
        self.assertEqual(
            results[0][
                "retrieval_method"
            ],
            "hybrid",
        )


if __name__ == "__main__":
    unittest.main()
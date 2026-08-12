import unittest
from unittest.mock import patch

from app.core.config import settings
from app.services.rag_service import (
    RAGService,
)


class RAGContextOptimizationTests(
    unittest.TestCase
):
    def test_narrow_qa_uses_base_top_k(
        self,
    ) -> None:
        with (
            patch.object(
                settings,
                "retrieval_top_k",
                3,
            ),
            patch.object(
                settings,
                "retrieval_candidate_k",
                10,
            ),
            patch.object(
                settings,
                "retrieval_adaptive_top_k_enabled",
                True,
            ),
            patch.object(
                settings,
                "retrieval_adaptive_top_k_max",
                5,
            ),
        ):
            top_k = RAGService._qa_top_k(
                "What does HbA1c 7.2% mean "
                "in this document?"
            )

        self.assertEqual(
            top_k,
            3,
        )

    def test_broad_qa_uses_adaptive_top_k(
        self,
    ) -> None:
        with (
            patch.object(
                settings,
                "retrieval_top_k",
                3,
            ),
            patch.object(
                settings,
                "retrieval_candidate_k",
                10,
            ),
            patch.object(
                settings,
                "retrieval_adaptive_top_k_enabled",
                True,
            ),
            patch.object(
                settings,
                "retrieval_adaptive_top_k_max",
                5,
            ),
        ):
            top_k = RAGService._qa_top_k(
                "List all medications documented."
            )

        self.assertEqual(
            top_k,
            5,
        )

    def test_adaptive_top_k_can_be_disabled(
        self,
    ) -> None:
        with (
            patch.object(
                settings,
                "retrieval_top_k",
                3,
            ),
            patch.object(
                settings,
                "retrieval_adaptive_top_k_enabled",
                False,
            ),
        ):
            top_k = RAGService._qa_top_k(
                "List all medications documented."
            )

        self.assertEqual(
            top_k,
            3,
        )


if __name__ == "__main__":
    unittest.main()
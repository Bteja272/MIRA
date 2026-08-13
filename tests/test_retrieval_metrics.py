import unittest

from evaluation.retrieval_metrics import (
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
)


class RetrievalMetricTests(
    unittest.TestCase
):
    def test_recall_at_k(
        self,
    ) -> None:
        score = recall_at_k(
            retrieved_chunk_ids=[
                "a",
                "b",
                "c",
            ],
            relevant_chunk_ids={
                "a",
                "c",
            },
            k=2,
        )

        self.assertEqual(
            score,
            0.5,
        )

    def test_precision_at_k_uses_returned_results(
        self,
    ) -> None:
        score = precision_at_k(
            retrieved_chunk_ids=[
                "a",
                "x",
            ],
            relevant_chunk_ids={
                "a",
            },
            k=5,
        )

        self.assertEqual(
            score,
            0.5,
        )

    def test_reciprocal_rank(
        self,
    ) -> None:
        score = reciprocal_rank(
            retrieved_chunk_ids=[
                "x",
                "y",
                "relevant",
            ],
            relevant_chunk_ids={
                "relevant",
            },
        )

        self.assertAlmostEqual(
            score,
            1 / 3,
        )

    def test_invalid_k_raises(
        self,
    ) -> None:
        with self.assertRaises(
            ValueError
        ):
            recall_at_k(
                retrieved_chunk_ids=[],
                relevant_chunk_ids={
                    "a",
                },
                k=0,
            )


if __name__ == "__main__":
    unittest.main()
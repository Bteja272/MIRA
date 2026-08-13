import unittest
from unittest.mock import patch

from evaluation.corpus_loader import (
    EvaluationCorpus,
    RetrievalCase,
)
from evaluation.retrieval_evaluator import (
    RetrievalEvaluator,
)


class RetrievalEvaluatorTests(
    unittest.TestCase
):
    def setUp(self) -> None:
        self.corpus = EvaluationCorpus(
            version="test",
            description="synthetic",
            evaluation_user={
                "user_id": "mira-eval-test",
                "email": (
                    "mira-eval-test@example.invalid"
                ),
            },
            documents=[],
            retrieval_cases=[
                RetrievalCase(
                    case_id="case-1",
                    query="HbA1c?",
                    document_ids=[
                        "doc-1",
                    ],
                    relevant_chunk_ids=[
                        "chunk-good",
                    ],
                )
            ],
        )

    @patch(
        "evaluation.retrieval_evaluator."
        "RetrievalService.retrieve"
    )
    def test_case_metrics_use_retrieved_chunk_ids(
        self,
        mock_retrieve,
    ) -> None:
        mock_retrieve.return_value = [
            {
                "chunk_id": "chunk-noise",
            },
            {
                "chunk_id": "chunk-good",
            },
            {
                "chunk_id": "chunk-other",
            },
        ]

        evaluator = RetrievalEvaluator(
            corpus=self.corpus,
            ks=[
                1,
                3,
            ],
        )

        result = evaluator.evaluate_case(
            self.corpus
            .retrieval_cases[0]
        )

        self.assertEqual(
            result["recall_at_k"]["1"],
            0.0,
        )
        self.assertEqual(
            result["recall_at_k"]["3"],
            1.0,
        )
        self.assertEqual(
            result["precision_at_k"]["3"],
            round(
                1 / 3,
                6,
            ),
        )
        self.assertEqual(
            result["reciprocal_rank"],
            0.5,
        )

    @patch(
        "evaluation.retrieval_evaluator."
        "RetrievalService.retrieve"
    )
    def test_warm_up_is_discarded(
        self,
        mock_retrieve,
    ) -> None:
        mock_retrieve.return_value = []

        evaluator = RetrievalEvaluator(
            corpus=self.corpus,
            ks=[
                1,
                3,
            ],
        )

        evaluator.warm_up()

        self.assertEqual(
            mock_retrieve.call_count,
            1,
        )


if __name__ == "__main__":
    unittest.main()
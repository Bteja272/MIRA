import logging
import unittest
from unittest.mock import (
    Mock,
    patch,
)

from app.core.config import settings
from app.services.cross_encoder_reranker_service import (
    CrossEncoderRerankerService,
)


def _candidate(
    chunk_id: str,
    text: str,
    hybrid_score: float,
) -> dict:
    return {
        "chunk_id": chunk_id,
        "document_id": "doc-1",
        "source": "synthetic.txt",
        "document_type": "lab_report",
        "page_number": 1,
        "chunk_index": 0,
        "similarity_score": 0.8,
        "document_position": 1,
        "text": text,
        "semantic_rank": 1,
        "lexical_rank": 1,
        "lexical_score": 1.0,
        "hybrid_score": hybrid_score,
        "retrieval_method": "hybrid",
    }


class CrossEncoderRerankerServiceTests(
    unittest.TestCase
):
    def tearDown(self) -> None:
        (
            CrossEncoderRerankerService
            ._model
        ) = None

    @patch(
        "app.services."
        "cross_encoder_reranker_service."
        "CrossEncoder"
    )
    def test_rerank_orders_by_cross_encoder_score(
        self,
        mock_cross_encoder,
    ) -> None:
        model = Mock()
        model.predict.return_value = [
            -1.25,
            4.75,
        ]
        mock_cross_encoder.return_value = (
            model
        )

        candidates = [
            _candidate(
                "chunk-a",
                "Routine follow-up.",
                0.04,
            ),
            _candidate(
                "chunk-b",
                (
                    "Medication list: "
                    "lisinopril 10 mg."
                ),
                0.03,
            ),
        ]

        with self.assertLogs(
            (
                "app.services."
                "cross_encoder_reranker_service"
            ),
            level=logging.INFO,
        ) as captured:
            results = (
                CrossEncoderRerankerService
                .rerank(
                    query=(
                        "Is lisinopril "
                        "10 mg listed?"
                    ),
                    candidates=candidates,
                    top_k=2,
                )
            )

        self.assertEqual(
            results[0]["chunk_id"],
            "chunk-b",
        )
        self.assertEqual(
            results[0]["rerank_rank"],
            1,
        )
        self.assertEqual(
            results[0]["rerank_score"],
            4.75,
        )
        self.assertEqual(
            results[0][
                "retrieval_method"
            ],
            "hybrid_reranked",
        )

        joined_logs = "\n".join(
            captured.output
        )

        self.assertIn(
            "reranker_model_loaded",
            joined_logs,
        )
        self.assertIn(
            "reranker_completed",
            joined_logs,
        )
        self.assertIn(
            "model_was_warm=False",
            joined_logs,
        )

        model.predict.assert_called_once()

    def test_warm_model_is_reused(
        self,
    ) -> None:
        model = Mock()
        model.predict.return_value = [
            2.0,
        ]

        (
            CrossEncoderRerankerService
            ._model
        ) = model

        with self.assertLogs(
            (
                "app.services."
                "cross_encoder_reranker_service"
            ),
            level=logging.INFO,
        ) as captured:
            results = (
                CrossEncoderRerankerService
                .rerank(
                    query="HbA1c",
                    candidates=[
                        _candidate(
                            "chunk-a",
                            "HbA1c 7.2%",
                            0.02,
                        )
                    ],
                    top_k=1,
                )
            )

        self.assertEqual(
            results[0]["chunk_id"],
            "chunk-a",
        )

        joined_logs = "\n".join(
            captured.output
        )

        self.assertNotIn(
            "reranker_model_loaded",
            joined_logs,
        )
        self.assertIn(
            "model_was_warm=True",
            joined_logs,
        )

    def test_empty_candidates_do_not_load_model(
        self,
    ) -> None:
        results = (
            CrossEncoderRerankerService
            .rerank(
                query="HbA1c",
                candidates=[],
                top_k=3,
            )
        )

        self.assertEqual(
            results,
            [],
        )
        self.assertFalse(
            CrossEncoderRerankerService
            .is_model_loaded()
        )


if __name__ == "__main__":
    unittest.main()
import unittest
from pathlib import Path

from evaluation.corpus_loader import (
    EvaluationCorpus,
)


class RetrievalCorpusTests(
    unittest.TestCase
):
    def test_bundled_corpus_is_valid(
        self,
    ) -> None:
        root = (
            Path(__file__)
            .resolve()
            .parents[1]
        )

        corpus = (
            EvaluationCorpus.load(
                root
                / "evaluation"
                / "corpus"
                / "retrieval_corpus.json"
            )
        )

        self.assertEqual(
            corpus.version,
            "1.0",
        )
        self.assertGreaterEqual(
            len(corpus.documents),
            8,
        )
        self.assertGreaterEqual(
            len(
                corpus.retrieval_cases
            ),
            12,
        )

        self.assertTrue(
            corpus.evaluation_user[
                "user_id"
            ].startswith(
                "mira-eval"
            )
        )


if __name__ == "__main__":
    unittest.main()
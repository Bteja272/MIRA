import unittest
from pathlib import Path

from evaluation.corpus_loader import (
    EvaluationCorpus,
)
from evaluation.quality_corpus_loader import (
    QualityCorpus,
)


class QualityCorpusTests(
    unittest.TestCase
):
    def test_bundled_quality_corpus_is_valid(
        self,
    ) -> None:
        repo_root = (
            Path(__file__)
            .resolve()
            .parents[1]
        )

        retrieval_corpus = (
            EvaluationCorpus.load(
                repo_root
                / "evaluation"
                / "corpus"
                / "retrieval_corpus.json"
            )
        )

        quality_corpus = (
            QualityCorpus.load(
                repo_root
                / "evaluation"
                / "corpus"
                / "quality_cases.json",
                retrieval_corpus=(
                    retrieval_corpus
                ),
            )
        )

        self.assertEqual(
            quality_corpus.version,
            "1.0",
        )
        self.assertGreaterEqual(
            len(
                quality_corpus
                .rag_cases
            ),
            6,
        )
        self.assertGreaterEqual(
            len(
                quality_corpus
                .extraction_cases
            ),
            4,
        )


if __name__ == "__main__":
    unittest.main()
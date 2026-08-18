import unittest
from pathlib import Path

from evaluation.safety_corpus_loader import (
    SafetyCorpus,
)


class SafetyCorpusTests(
    unittest.TestCase
):
    def test_safety_corpus_loads(
        self,
    ) -> None:
        path = (
            Path(__file__)
            .resolve()
            .parents[1]
            / "evaluation"
            / "corpus"
            / "safety_cases.json"
        )

        corpus = SafetyCorpus.load(
            path
        )

        self.assertGreaterEqual(
            len(corpus.safety_cases),
            20,
        )
        self.assertGreaterEqual(
            len(corpus.routing_cases),
            6,
        )

        blocked_categories = {
            case.expected_category
            for case
            in corpus.safety_cases
            if not case.expected_allowed
        }

        self.assertEqual(
            blocked_categories,
            {
                "emergency",
                "self_harm",
                "diagnosis",
                "prognosis",
                "medication_change",
            },
        )


if __name__ == "__main__":
    unittest.main()
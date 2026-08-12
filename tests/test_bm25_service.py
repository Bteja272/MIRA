import unittest

from app.services.bm25_service import (
    BM25Service,
)


class BM25ServiceTests(
    unittest.TestCase
):
    def test_exact_medical_code_ranks_matching_chunk_first(
        self,
    ) -> None:
        documents = [
            (
                "Assessment: type 2 diabetes "
                "mellitus. ICD-10 E11.9."
            ),
            (
                "Blood pressure reviewed. "
                "No diagnosis code listed."
            ),
            (
                "Medication list includes "
                "metformin."
            ),
        ]

        ranked = BM25Service.rank(
            query="What does E11.9 refer to?",
            documents=documents,
            top_k=3,
        )

        self.assertTrue(ranked)
        self.assertEqual(
            ranked[0][0],
            0,
        )
        self.assertGreater(
            ranked[0][1],
            0,
        )

    def test_medication_and_dose_terms_rank_matching_chunk_first(
        self,
    ) -> None:
        documents = [
            (
                "Medication: lisinopril "
                "10 mg daily."
            ),
            (
                "Medication: atorvastatin "
                "20 mg daily."
            ),
            (
                "The patient returned for "
                "routine follow-up."
            ),
        ]

        ranked = BM25Service.rank(
            query="lisinopril 10 mg",
            documents=documents,
            top_k=3,
        )

        self.assertTrue(ranked)
        self.assertEqual(
            ranked[0][0],
            0,
        )

    def test_no_lexical_overlap_returns_no_results(
        self,
    ) -> None:
        ranked = BM25Service.rank(
            query="HbA1c",
            documents=[
                "Chest x-ray reviewed.",
                "No medication changes.",
            ],
            top_k=3,
        )

        self.assertEqual(
            ranked,
            [],
        )

    def test_tokenizer_preserves_medical_code_punctuation(
        self,
    ) -> None:
        tokens = BM25Service.tokenize(
            "ICD-10 E11.9 and A1C 7.2%"
        )

        self.assertIn(
            "icd-10",
            tokens,
        )
        self.assertIn(
            "e11.9",
            tokens,
        )
        self.assertIn(
            "7.2",
            tokens,
        )


if __name__ == "__main__":
    unittest.main()
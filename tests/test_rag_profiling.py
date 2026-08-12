import logging
import unittest
from unittest.mock import (
    Mock,
    patch,
)

from langchain_core.documents import (
    Document as LangChainDocument,
)

from app.services.embedding_service import (
    EmbeddingService,
)
from app.services.rag_service import (
    RAGService,
)


class RAGProfilingTests(
    unittest.TestCase
):
    def setUp(self) -> None:
        self.document = (
            LangChainDocument(
                page_content=(
                    "Hemoglobin A1c: 7.2%"
                ),
                metadata={
                    "chunk_id": "chunk-1",
                    "document_id": "doc-1",
                    "source": "synthetic.txt",
                    "document_type": (
                        "lab_report"
                    ),
                    "page_number": 1,
                    "chunk_index": 0,
                    "similarity_score": 0.91,
                    "document_position": 1,
                },
            )
        )

    @patch(
        "app.services.rag_service."
        "LangChainRetrieverService."
        "to_source_dicts"
    )
    @patch(
        "app.services.rag_service."
        "MedicalPromptService."
        "ensure_disclaimer"
    )
    @patch(
        "app.services.rag_service."
        "ResponseValidationService."
        "sanitize_document_answer"
    )
    @patch(
        "app.services.rag_service."
        "LLMService.generate_response"
    )
    @patch(
        "app.services.rag_service."
        "PromptService.build_prompt"
    )
    @patch(
        "app.services.rag_service."
        "DocumentMergeService."
        "merge_documents"
    )
    @patch(
        "app.services.rag_service."
        "LangChainRetrieverService."
        "retrieve"
    )
    def test_qa_path_emits_stage_profile_log(
        self,
        mock_retrieve,
        mock_merge,
        mock_prompt,
        mock_llm,
        mock_validate,
        mock_disclaimer,
        mock_sources,
    ) -> None:
        mock_retrieve.return_value = [
            self.document
        ]
        mock_merge.return_value = [
            self.document
        ]
        mock_prompt.return_value = (
            "Synthetic prompt"
        )
        mock_llm.return_value = (
            "Synthetic answer"
        )
        mock_validate.return_value = (
            "Synthetic answer"
        )
        mock_disclaimer.return_value = (
            "Synthetic answer\n\nDisclaimer"
        )
        mock_sources.return_value = [
            {
                "source_number": 1,
                "document_id": "doc-1",
            }
        ]

        with self.assertLogs(
            "app.services.rag_service",
            level=logging.INFO,
        ) as captured:
            result = RAGService.query(
                query=(
                    "What does my A1c "
                    "result say?"
                ),
                document_ids=[
                    "doc-1",
                ],
                user_id="user-1",
            )

        joined_logs = "\n".join(
            captured.output
        )

        self.assertIn(
            "rag_query_completed",
            joined_logs,
        )
        self.assertIn(
            "task=qa",
            joined_logs,
        )
        self.assertIn(
            "retrieval_ms",
            joined_logs,
        )
        self.assertIn(
            "llm_generation_ms",
            joined_logs,
        )
        self.assertIn(
            "total_ms",
            joined_logs,
        )
        self.assertEqual(
            result["answer"],
            (
                "Synthetic answer\n\n"
                "Disclaimer"
            ),
        )

    @patch(
        "app.services.rag_service."
        "MedicalPromptService."
        "ensure_disclaimer"
    )
    @patch(
        "app.services.rag_service."
        "LangChainRetrieverService."
        "retrieve"
    )
    def test_empty_retrieval_still_logs_profile(
        self,
        mock_retrieve,
        mock_disclaimer,
    ) -> None:
        mock_retrieve.return_value = []
        mock_disclaimer.return_value = (
            "No information\n\nDisclaimer"
        )

        with self.assertLogs(
            "app.services.rag_service",
            level=logging.INFO,
        ) as captured:
            result = RAGService.query(
                query="What is documented?",
                document_ids=[
                    "doc-1",
                ],
                user_id="user-1",
            )

        joined_logs = "\n".join(
            captured.output
        )

        self.assertIn(
            "rag_query_completed",
            joined_logs,
        )
        self.assertIn(
            "retrieved_count=0",
            joined_logs,
        )
        self.assertEqual(
            result["sources"],
            [],
        )


class EmbeddingProfilingTests(
    unittest.TestCase
):
    def tearDown(self) -> None:
        EmbeddingService._model = None

    @patch(
        "app.services.embedding_service."
        "SentenceTransformer"
    )
    def test_cold_embedding_logs_model_load(
        self,
        mock_transformer,
    ) -> None:
        vector = Mock()
        vector.tolist.return_value = [
            0.1,
            0.2,
        ]

        model = Mock()
        model.encode.return_value = vector
        mock_transformer.return_value = (
            model
        )

        EmbeddingService._model = None

        with self.assertLogs(
            "app.services.embedding_service",
            level=logging.INFO,
        ) as captured:
            result = (
                EmbeddingService.embed_text(
                    "synthetic"
                )
            )

        joined_logs = "\n".join(
            captured.output
        )

        self.assertEqual(
            result,
            [
                0.1,
                0.2,
            ],
        )
        self.assertIn(
            "embedding_model_loaded",
            joined_logs,
        )
        self.assertIn(
            "model_was_warm=False",
            joined_logs,
        )

    def test_warm_embedding_skips_model_load_log(
        self,
    ) -> None:
        vector = Mock()
        vector.tolist.return_value = [
            0.3,
        ]

        model = Mock()
        model.encode.return_value = vector
        EmbeddingService._model = model

        with self.assertLogs(
            "app.services.embedding_service",
            level=logging.INFO,
        ) as captured:
            result = (
                EmbeddingService.embed_text(
                    "synthetic"
                )
            )

        joined_logs = "\n".join(
            captured.output
        )

        self.assertEqual(
            result,
            [
                0.3,
            ],
        )
        self.assertNotIn(
            "embedding_model_loaded",
            joined_logs,
        )
        self.assertIn(
            "model_was_warm=True",
            joined_logs,
        )


if __name__ == "__main__":
    unittest.main()
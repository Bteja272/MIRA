import unittest
from unittest.mock import patch

from langchain_core.documents import (
    Document as LangChainDocument,
)

from app.services.rag_service import (
    RAGService,
)


class RAGDocumentProcessingTests(
    unittest.TestCase
):
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
        "LangChainRetrieverService."
        "retrieve_documents"
    )
    def test_multi_document_context_is_merged(
        self,
        mock_retrieve_documents,
        mock_build_prompt,
        mock_generate_response,
    ):
        selected_ids = [
            "lab-id",
            "discharge-id",
        ]

        mock_retrieve_documents.return_value = [
            LangChainDocument(
                page_content=(
                    "LAB RESULT\n"
                    "Result: 7.2 %"
                ),
                metadata={
                    "chunk_id": "lab-0",
                    "document_id": "lab-id",
                    "source": "lab.txt",
                    "document_type": (
                        "lab_report"
                    ),
                    "document_position": 1,
                    "chunk_index": 0,
                    "page_number": None,
                    "similarity_score": None,
                },
            ),
            LangChainDocument(
                page_content=(
                    "Result: 7.2 %\n"
                    "Flag: High"
                ),
                metadata={
                    "chunk_id": "lab-1",
                    "document_id": "lab-id",
                    "source": "lab.txt",
                    "document_type": (
                        "lab_report"
                    ),
                    "document_position": 1,
                    "chunk_index": 1,
                    "page_number": None,
                    "similarity_score": None,
                },
            ),
            LangChainDocument(
                page_content=(
                    "DISCHARGE SUMMARY"
                ),
                metadata={
                    "chunk_id": (
                        "discharge-0"
                    ),
                    "document_id": (
                        "discharge-id"
                    ),
                    "source": (
                        "discharge.txt"
                    ),
                    "document_type": (
                        "discharge_summary"
                    ),
                    "document_position": 2,
                    "chunk_index": 0,
                    "page_number": None,
                    "similarity_score": None,
                },
            ),
        ]

        mock_build_prompt.return_value = (
            "merged prompt"
        )

        mock_generate_response.return_value = (
            "Result is above reference range.\n"
            "Documented flag: High."
        )

        result = RAGService.query(
            query=(
                "Give me an overview "
                "of these documents."
            ),
            document_ids=selected_ids,
        )

        prompt_documents = (
            mock_build_prompt
            .call_args
            .kwargs["documents"]
        )

        self.assertEqual(
            len(prompt_documents),
            2,
        )

        self.assertEqual(
            len(result["sources"]),
            2,
        )

        self.assertNotIn(
            "above reference range",
            result["answer"].lower(),
        )

        self.assertIn(
            "Documented flag: High",
            result["answer"],
        )

        self.assertEqual(
            result["document_ids"],
            selected_ids,
        )


if __name__ == "__main__":
    unittest.main()
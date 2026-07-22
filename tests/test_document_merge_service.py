import unittest

from langchain_core.documents import (
    Document as LangChainDocument,
)

from app.services.document_merge_service import (
    DocumentMergeService,
)


class DocumentMergeServiceTests(
    unittest.TestCase
):
    def test_merges_chunks_and_removes_overlap(
        self,
    ):
        overlapping_text = (
            "LDL Cholesterol\n"
            "Result: 121 mg/dL\n"
            "Reference Range: Below 100 mg/dL\n"
            "Flag: High"
        )

        documents = [
            LangChainDocument(
                page_content=(
                    "Total Cholesterol\n"
                    "Result: 196 mg/dL\n"
                    "Flag: Normal\n"
                    f"{overlapping_text}"
                ),
                metadata={
                    "chunk_id": "lab-0",
                    "document_id": "lab",
                    "source": "lab.txt",
                    "document_type": (
                        "lab_report"
                    ),
                    "document_position": 1,
                    "page_number": None,
                    "chunk_index": 0,
                    "similarity_score": None,
                },
            ),
            LangChainDocument(
                page_content=(
                    f"{overlapping_text}\n"
                    "HDL Cholesterol\n"
                    "Result: 48 mg/dL\n"
                    "Flag: Normal"
                ),
                metadata={
                    "chunk_id": "lab-1",
                    "document_id": "lab",
                    "source": "lab.txt",
                    "document_type": (
                        "lab_report"
                    ),
                    "document_position": 1,
                    "page_number": None,
                    "chunk_index": 1,
                    "similarity_score": None,
                },
            ),
            LangChainDocument(
                page_content=(
                    "DISCHARGE DIAGNOSES\n"
                    "1. Type 2 diabetes mellitus"
                ),
                metadata={
                    "chunk_id": "discharge-0",
                    "document_id": (
                        "discharge"
                    ),
                    "source": (
                        "discharge.txt"
                    ),
                    "document_type": (
                        "discharge_summary"
                    ),
                    "document_position": 2,
                    "page_number": None,
                    "chunk_index": 0,
                    "similarity_score": None,
                },
            ),
        ]

        merged = (
            DocumentMergeService
            .merge_documents(
                documents
            )
        )

        self.assertEqual(
            len(merged),
            2,
        )

        lab_document = merged[0]

        self.assertEqual(
            lab_document.metadata[
                "document_position"
            ],
            1,
        )

        self.assertEqual(
            lab_document.metadata[
                "merged_chunk_count"
            ],
            2,
        )

        self.assertEqual(
            lab_document.page_content.count(
                overlapping_text
            ),
            1,
        )

        self.assertIn(
            "HDL Cholesterol",
            lab_document.page_content,
        )

        self.assertEqual(
            merged[1].metadata[
                "document_position"
            ],
            2,
        )


if __name__ == "__main__":
    unittest.main()
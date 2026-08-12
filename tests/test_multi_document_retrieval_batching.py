import unittest
from types import SimpleNamespace
from unittest.mock import (
    Mock,
    patch,
)

from app.services.retrieval_service import (
    RetrievalService,
)


def _chunk(
    *,
    document_id: str,
    chunk_id: str,
    page_number: int,
    chunk_index: int,
    text: str,
):
    return SimpleNamespace(
        chunk_id=chunk_id,
        document_id=document_id,
        page_number=page_number,
        chunk_index=chunk_index,
        text=text,
    )


def _document(
    *,
    document_id: str,
    filename: str,
):
    return SimpleNamespace(
        document_id=document_id,
        original_filename=filename,
        source=filename,
        stored_filename=filename,
        document_type="synthetic",
    )


class MultiDocumentRetrievalBatchingTests(
    unittest.TestCase
):
    @patch(
        "app.services.retrieval_service."
        "SessionLocal"
    )
    def test_multi_document_load_uses_one_database_query(
        self,
        mock_session_local,
    ) -> None:
        db = Mock()
        mock_session_local.return_value = (
            db
        )

        doc_a = _document(
            document_id="doc-a",
            filename="a.txt",
        )
        doc_b = _document(
            document_id="doc-b",
            filename="b.txt",
        )

        # Intentionally return rows out of requested order.
        db.execute.return_value.all.return_value = [
            (
                _chunk(
                    document_id="doc-b",
                    chunk_id="b-2",
                    page_number=2,
                    chunk_index=1,
                    text="B second",
                ),
                doc_b,
            ),
            (
                _chunk(
                    document_id="doc-a",
                    chunk_id="a-1",
                    page_number=1,
                    chunk_index=0,
                    text="A first",
                ),
                doc_a,
            ),
            (
                _chunk(
                    document_id="doc-b",
                    chunk_id="b-1",
                    page_number=1,
                    chunk_index=0,
                    text="B first",
                ),
                doc_b,
            ),
        ]

        results = (
            RetrievalService
            .retrieve_documents(
                document_ids=[
                    "doc-b",
                    "doc-a",
                ],
                user_id="user-1",
            )
        )

        self.assertEqual(
            db.execute.call_count,
            1,
        )

        self.assertEqual(
            [
                result["chunk_id"]
                for result in results
            ],
            [
                "b-1",
                "b-2",
                "a-1",
            ],
        )

        self.assertEqual(
            [
                result[
                    "document_position"
                ]
                for result in results
            ],
            [
                1,
                1,
                2,
            ],
        )

        db.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
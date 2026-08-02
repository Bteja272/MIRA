import unittest
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import HTTPException

from app.api.routes import (
    documents,
    extractions,
    query,
)
from app.schemas.extraction_api import (
    ExtractionGenerateRequest,
)
from app.schemas.query import (
    QueryRequest,
)
from app.services.medical_extraction_service import (
    MedicalExtractionNotFoundError,
)


class BackendAuthorizationMatrixTests(
    unittest.TestCase
):
    def setUp(self):
        self.user = SimpleNamespace(
            user_id="user-a",
        )

    @patch.object(
        documents.DocumentService,
        "get_document",
        return_value=None,
    )
    def test_document_lookup_uses_owner_scope(
        self,
        get_document,
    ):
        with self.assertRaises(
            HTTPException
        ) as context:
            documents.get_document(
                document_id="doc-b",
                current_user=self.user,
            )

        self.assertEqual(
            context.exception.status_code,
            404,
        )

        get_document.assert_called_once_with(
            document_id="doc-b",
            user_id="user-a",
        )

    @patch.object(
        documents.DocumentService,
        "delete_document",
        return_value=None,
    )
    def test_document_delete_uses_owner_scope(
        self,
        delete_document,
    ):
        with self.assertRaises(
            HTTPException
        ) as context:
            documents.delete_document(
                document_id="doc-b",
                current_user=self.user,
            )

        self.assertEqual(
            context.exception.status_code,
            404,
        )

        self.assertEqual(
            delete_document.call_args.kwargs[
                "user_id"
            ],
            "user-a",
        )

    @patch.object(
        documents.DocumentService,
        "delete_document",
        side_effect=RuntimeError(
            "/private/internal/path"
        ),
    )
    def test_document_delete_hides_internal_error(
        self,
        _delete_document,
    ):
        with self.assertRaises(
            HTTPException
        ) as context:
            documents.delete_document(
                document_id="doc-a",
                current_user=self.user,
            )

        self.assertEqual(
            context.exception.status_code,
            500,
        )

        self.assertNotIn(
            "/private/internal/path",
            str(context.exception.detail),
        )

    @patch.object(
        query.LangGraphAgentService,
        "query",
    )
    @patch.object(
        query.DocumentService,
        "get_existing_document_ids",
        return_value=[],
    )
    def test_query_rejects_unowned_document(
        self,
        _existing_ids,
        agent_query,
    ):
        request = QueryRequest(
            query="Summarize this.",
            document_ids=[
                "doc-b"
            ],
        )

        with self.assertRaises(
            HTTPException
        ) as context:
            query.query_agent(
                request=request,
                current_user=self.user,
            )

        self.assertEqual(
            context.exception.status_code,
            404,
        )

        agent_query.assert_not_called()

    @patch.object(
        extractions
        .MedicalExtractionPersistenceService,
        "get",
        return_value=None,
    )
    def test_extraction_lookup_uses_owner_scope(
        self,
        get_extraction,
    ):
        with self.assertRaises(
            HTTPException
        ) as context:
            extractions.get_document_extraction(
                document_id="doc-b",
                current_user=self.user,
            )

        self.assertEqual(
            context.exception.status_code,
            404,
        )

        get_extraction.assert_called_once_with(
            document_id="doc-b",
            user_id="user-a",
        )

    @patch.object(
        extractions
        .MedicalExtractionPersistenceService,
        "get",
        return_value=None,
    )
    @patch.object(
        extractions.MedicalExtractionService,
        "extract",
        side_effect=(
            MedicalExtractionNotFoundError(
                "not found"
            )
        ),
    )
    def test_extraction_generation_hides_cross_user_document(
        self,
        _extract,
        _get,
    ):
        with self.assertRaises(
            HTTPException
        ) as context:
            extractions.generate_document_extraction(
                document_id="doc-b",
                request=(
                    ExtractionGenerateRequest(
                        replace_existing=False
                    )
                ),
                current_user=self.user,
            )

        self.assertEqual(
            context.exception.status_code,
            404,
        )


if __name__ == "__main__":
    unittest.main()
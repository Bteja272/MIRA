import unittest
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import HTTPException

from app.api.routes.documents import (
    get_document,
    list_documents,
)


class DocumentRouteOwnershipTests(
    unittest.TestCase
):
    @patch(
        "app.api.routes.documents."
        "DocumentService.list_documents"
    )
    def test_list_uses_authenticated_user(
        self,
        mock_list_documents,
    ):
        mock_list_documents.return_value = []

        current_user = (
            SimpleNamespace(
                user_id="user-123"
            )
        )

        result = list_documents(
            current_user=current_user
        )

        mock_list_documents.assert_called_once_with(
            user_id="user-123"
        )

        self.assertEqual(
            result["count"],
            0,
        )

    @patch(
        "app.api.routes.documents."
        "DocumentService.get_document"
    )
    def test_unowned_document_returns_404(
        self,
        mock_get_document,
    ):
        mock_get_document.return_value = None

        current_user = (
            SimpleNamespace(
                user_id="user-123"
            )
        )

        with self.assertRaises(
            HTTPException
        ) as context:
            get_document(
                document_id=(
                    "another-users-document"
                ),
                current_user=(
                    current_user
                ),
            )

        self.assertEqual(
            context.exception.status_code,
            404,
        )

        mock_get_document.assert_called_once_with(
            document_id=(
                "another-users-document"
            ),
            user_id="user-123",
        )


if __name__ == "__main__":
    unittest.main()
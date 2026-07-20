import tempfile
import unittest
from pathlib import Path

from app.services.document_service import (
    DocumentService,
)


class DocumentServiceTests(
    unittest.TestCase
):
    def test_resolves_safe_stored_filename(self):
        with tempfile.TemporaryDirectory() as directory:
            upload_directory = Path(directory)

            result = (
                DocumentService
                ._resolve_stored_path(
                    upload_directory=(
                        upload_directory
                    ),
                    stored_filename=(
                        "document-id.txt"
                    ),
                )
            )

            self.assertEqual(
                result,
                (
                    upload_directory
                    / "document-id.txt"
                ).resolve(),
            )

    def test_rejects_parent_directory_path(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(
                ValueError
            ):
                (
                    DocumentService
                    ._resolve_stored_path(
                        upload_directory=Path(
                            directory
                        ),
                        stored_filename=(
                            "../secret.txt"
                        ),
                    )
                )

    def test_rejects_forward_slash(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(
                ValueError
            ):
                (
                    DocumentService
                    ._resolve_stored_path(
                        upload_directory=Path(
                            directory
                        ),
                        stored_filename=(
                            "folder/document.txt"
                        ),
                    )
                )

    def test_rejects_backslash(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(
                ValueError
            ):
                (
                    DocumentService
                    ._resolve_stored_path(
                        upload_directory=Path(
                            directory
                        ),
                        stored_filename=(
                            r"folder\document.txt"
                        ),
                    )
                )

    def test_rejects_empty_filename(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(
                ValueError
            ):
                (
                    DocumentService
                    ._resolve_stored_path(
                        upload_directory=Path(
                            directory
                        ),
                        stored_filename="",
                    )
                )


if __name__ == "__main__":
    unittest.main()
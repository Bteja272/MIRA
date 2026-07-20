from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader


@dataclass
class RawPageDocument:
    document_id: str
    source: str
    page_number: int | None
    text: str


class DocumentLoaderService:
    @classmethod
    def load_document(
        cls,
        file_path: str | Path,
        document_id: str,
        source_name: str | None = None,
    ) -> list[RawPageDocument]:
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(
                f"Document does not exist: {path}"
            )

        source = source_name or path.name
        extension = path.suffix.lower()

        if extension == ".txt":
            return cls._load_text(
                path=path,
                document_id=document_id,
                source=source,
            )

        if extension == ".pdf":
            return cls._load_pdf(
                path=path,
                document_id=document_id,
                source=source,
            )

        raise ValueError(
            f"Unsupported document type: {extension}"
        )

    @staticmethod
    def _load_text(
        path: Path,
        document_id: str,
        source: str,
    ) -> list[RawPageDocument]:
        text = path.read_text(
            encoding="utf-8",
            errors="replace",
        )

        return [
            RawPageDocument(
                document_id=document_id,
                source=source,
                page_number=None,
                text=text,
            )
        ]

    @staticmethod
    def _load_pdf(
        path: Path,
        document_id: str,
        source: str,
    ) -> list[RawPageDocument]:
        reader = PdfReader(str(path))
        documents: list[RawPageDocument] = []

        for page_number, page in enumerate(
            reader.pages,
            start=1,
        ):
            documents.append(
                RawPageDocument(
                    document_id=document_id,
                    source=source,
                    page_number=page_number,
                    text=page.extract_text() or "",
                )
            )

        return documents
import hashlib
from pathlib import Path
from uuid import uuid4

from fastapi import (
    APIRouter,
    File,
    HTTPException,
    UploadFile,
)

from app.services.chunking_service import TextChunkingService
from app.services.cleaner_service import TextCleanerService
from app.services.document_classifier import DocumentClassifier
from app.services.indexing_service import IndexingService
from app.services.loader_service import DocumentLoaderService


router = APIRouter(
    prefix="/ingest",
    tags=["ingestion"],
)

UPLOAD_DIRECTORY = Path("uploaded_files")
UPLOAD_DIRECTORY.mkdir(
    parents=True,
    exist_ok=True,
)

ALLOWED_EXTENSIONS = {
    ".pdf",
    ".txt",
}

MAX_UPLOAD_BYTES = 25 * 1024 * 1024


@router.post("")
async def ingest_file(
    file: UploadFile = File(...),
) -> dict:
    original_filename = Path(
        file.filename or ""
    ).name

    if not original_filename:
        raise HTTPException(
            status_code=400,
            detail="A valid filename is required.",
        )

    extension = Path(
        original_filename
    ).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported file type. "
                "Only PDF and TXT files are allowed."
            ),
        )

    document_id = str(uuid4())
    stored_filename = (
        f"{document_id}{extension}"
    )
    stored_path = (
        UPLOAD_DIRECTORY / stored_filename
    )

    file_hash = hashlib.sha256()
    file_size_bytes = 0

    try:
        with stored_path.open("wb") as destination:
            while True:
                data = await file.read(
                    1024 * 1024
                )

                if not data:
                    break

                file_size_bytes += len(data)

                if file_size_bytes > MAX_UPLOAD_BYTES:
                    raise HTTPException(
                        status_code=413,
                        detail=(
                            "The uploaded file exceeds "
                            "the 25 MB limit."
                        ),
                    )

                file_hash.update(data)
                destination.write(data)

        loaded_documents = (
            DocumentLoaderService.load_document(
                file_path=stored_path,
                document_id=document_id,
                source_name=original_filename,
            )
        )

        cleaned_documents = []

        for document in loaded_documents:
            cleaned_text = (
                TextCleanerService.clean_text(
                    document.text
                )
            )

            if not cleaned_text:
                continue

            document.text = cleaned_text
            cleaned_documents.append(document)

        if not cleaned_documents:
            raise HTTPException(
                status_code=400,
                detail=(
                    "No readable text was found "
                    "in the uploaded document."
                ),
            )

        complete_text = "\n\n".join(
            document.text
            for document in cleaned_documents
        )

        document_type = (
            DocumentClassifier.classify(
                text=complete_text,
                filename=original_filename,
            )
        )

        chunk_records = (
            TextChunkingService
            .build_chunk_records(
                cleaned_documents
            )
        )

        chunks_indexed = (
            IndexingService.index_document(
                document_id=document_id,
                source=original_filename,
                original_filename=original_filename,
                stored_filename=stored_filename,
                document_type=document_type,
                file_hash=file_hash.hexdigest(),
                file_size_bytes=file_size_bytes,
                chunk_records=chunk_records,
                user_id=None,
            )
        )

        return {
            "document_id": document_id,
            "filename": original_filename,
            "document_type": document_type,
            "file_size_bytes": file_size_bytes,
            "chunks_indexed": chunks_indexed,
            "message": (
                "Document indexed successfully"
            ),
        }

    except HTTPException:
        stored_path.unlink(
            missing_ok=True
        )
        raise

    except Exception as exc:
        stored_path.unlink(
            missing_ok=True
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Document ingestion failed: "
                f"{exc}"
            ),
        ) from exc

    finally:
        await file.close()
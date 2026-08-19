import hashlib
import logging
from pathlib import Path
from uuid import uuid4

from fastapi import (
    APIRouter,
    File,
    HTTPException,
    UploadFile,
    status,
)
from starlette.concurrency import (
    run_in_threadpool,
)

from app.api.dependencies.auth import (
    CurrentUser,
)
from app.core.notices import (
    DEVELOPMENT_PRIVACY_NOTICE,
)
from app.schemas.ingest import (
    IngestResponse,
)
from app.services.chunking_service import (
    TextChunkingService,
)
from app.services.cleaner_service import (
    TextCleanerService,
)
from app.services.document_classifier import (
    DocumentClassifier,
)
from app.services.document_service import (
    DocumentService,
)
from app.services.indexing_service import (
    IndexingService,
)
from app.services.loader_service import (
    DocumentLoaderService,
)


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/ingest",
    tags=["ingestion"],
)

UPLOAD_DIRECTORY = Path(
    "uploaded_files"
)

UPLOAD_DIRECTORY.mkdir(
    parents=True,
    exist_ok=True,
)

ALLOWED_EXTENSIONS = {
    ".pdf",
    ".txt",
}

MAX_UPLOAD_BYTES = (
    25 * 1024 * 1024
)


def _process_stored_document(
    *,
    stored_path: Path,
    stored_filename: str,
    original_filename: str,
    document_id: str,
    file_hash: str,
    file_size_bytes: int,
    user_id: str,
) -> dict:
    duplicate = (
        DocumentService
        .find_duplicate_by_hash(
            file_hash=file_hash,
            user_id=user_id,
        )
    )

    if duplicate is not None:
        stored_path.unlink(
            missing_ok=True
        )

        return {
            "duplicate": True,
            "existing_document_id": (
                duplicate["document_id"]
            ),
            "filename": (
                duplicate["filename"]
            ),
            "document_type": (
                duplicate["document_type"]
            ),
            "message": (
                "This file has already been "
                "uploaded to your account."
            ),
        }

    loaded_documents = (
        DocumentLoaderService
        .load_document(
            file_path=stored_path,
            document_id=document_id,
            source_name=original_filename,
        )
    )

    cleaned_documents = []

    for document in loaded_documents:
        cleaned_text = (
            TextCleanerService
            .clean_text(
                document.text
            )
        )

        if not cleaned_text:
            continue

        document.text = cleaned_text
        cleaned_documents.append(
            document
        )

    if not cleaned_documents:
        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
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
        DocumentClassifier
        .classify(
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
        IndexingService
        .index_document(
            document_id=document_id,
            source=original_filename,
            original_filename=(
                original_filename
            ),
            stored_filename=(
                stored_filename
            ),
            document_type=(
                document_type
            ),
            file_hash=file_hash,
            file_size_bytes=(
                file_size_bytes
            ),
            chunk_records=(
                chunk_records
            ),
            user_id=user_id,
        )
    )

    return {
        "duplicate": False,
        "document_id": document_id,
        "filename": original_filename,
        "document_type": document_type,
        "file_size_bytes": (
            file_size_bytes
        ),
        "chunks_indexed": (
            chunks_indexed
        ),
        "message": (
            "Document indexed successfully."
        ),
        "development_notice": (
            DEVELOPMENT_PRIVACY_NOTICE
        ),
    }


@router.post(
    "",
    response_model=IngestResponse,
    summary="Upload and index a medical document",
    description=(
        DEVELOPMENT_PRIVACY_NOTICE
    ),
)
async def ingest_file(
    current_user: CurrentUser,
    file: UploadFile = File(...),
) -> dict:
    original_filename = Path(
        file.filename or ""
    ).name

    if not original_filename:
        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=(
                "A valid filename is required."
            ),
        )

    extension = Path(
        original_filename
    ).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=(
                "Unsupported file type. "
                "Only PDF and TXT files "
                "are allowed."
            ),
        )

    document_id = str(
        uuid4()
    )

    stored_filename = (
        f"{document_id}{extension}"
    )

    stored_path = (
        UPLOAD_DIRECTORY
        / stored_filename
    )

    file_hash_builder = (
        hashlib.sha256()
    )

    file_size_bytes = 0

    try:
        with stored_path.open(
            "wb"
        ) as destination:
            while True:
                data = await file.read(
                    1024 * 1024
                )

                if not data:
                    break

                file_size_bytes += len(
                    data
                )

                if (
                    file_size_bytes
                    > MAX_UPLOAD_BYTES
                ):
                    raise HTTPException(
                        status_code=(
                            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
                        ),
                        detail=(
                            "The uploaded file exceeds "
                            "the 25 MB limit."
                        ),
                    )

                file_hash_builder.update(
                    data
                )

                destination.write(
                    data
                )

        if file_size_bytes == 0:
            raise HTTPException(
                status_code=(
                    status.HTTP_400_BAD_REQUEST
                ),
                detail=(
                    "The uploaded file is empty."
                ),
            )

        result = await run_in_threadpool(
            _process_stored_document,
            stored_path=stored_path,
            stored_filename=(
                stored_filename
            ),
            original_filename=(
                original_filename
            ),
            document_id=document_id,
            file_hash=(
                file_hash_builder.hexdigest()
            ),
            file_size_bytes=(
                file_size_bytes
            ),
            user_id=(
                current_user.user_id
            ),
        )

        return result

    except HTTPException:
        stored_path.unlink(
            missing_ok=True
        )

        raise

    except Exception as exc:
        stored_path.unlink(
            missing_ok=True
        )

        logger.exception(
            (
                "document_ingestion_failed "
                "user_id=%s "
                "document_id=%s"
            ),
            current_user.user_id,
            document_id,
        )

        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "Document ingestion failed."
            ),
        ) from exc

    finally:
        await file.close()
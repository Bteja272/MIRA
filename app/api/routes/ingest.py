import shutil
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.core.config import settings
from app.services.cleaner_service import TextCleanerService
from app.services.chunking_service import TextChunkingService
from app.services.indexing_service import IndexingService
from app.services.loader_service import DocumentLoaderService


router = APIRouter(tags=["Ingestion"])

UPLOAD_DIR = Path("uploaded_files")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".txt"}


@router.post("/ingest")
async def ingest_file(file: UploadFile = File(...)):
    filename = Path(file.filename or "").name

    if not filename:
        raise HTTPException(status_code=400, detail="A filename is required.")

    extension = Path(filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Only PDF and TXT files are supported.",
        )

    file_path = UPLOAD_DIR / filename

    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        loaded = DocumentLoaderService.load_document(str(file_path))
        all_chunks = []

        if isinstance(loaded, list):
            if not loaded:
                raise HTTPException(
                    status_code=400,
                    detail="The PDF does not contain any readable pages.",
                )

            document_id = loaded[0].document_id

            for page in loaded:
                cleaned = TextCleanerService.clean_text(page.text)

                chunks = TextChunkingService.build_chunk_records(
                    document_id=page.document_id,
                    source=page.source,
                    text=cleaned,
                    chunk_size=settings.chunk_size,
                    chunk_overlap=settings.chunk_overlap,
                    page_number=page.page_number,
                )
                all_chunks.extend(chunks)

        else:
            document_id = loaded.document_id
            cleaned = TextCleanerService.clean_text(loaded.text)

            chunks = TextChunkingService.build_chunk_records(
                document_id=loaded.document_id,
                source=loaded.source,
                text=cleaned,
                chunk_size=settings.chunk_size,
                chunk_overlap=settings.chunk_overlap,
            )
            all_chunks.extend(chunks)

        if not all_chunks:
            raise HTTPException(
                status_code=400,
                detail="No readable text was found in the document.",
            )

        IndexingService.index_chunks(all_chunks)

        return {
            "document_id": document_id,
            "filename": filename,
            "chunks_indexed": len(all_chunks),
            "message": "Document indexed successfully",
        }

    finally:
        await file.close()
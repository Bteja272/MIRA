from pathlib import Path

from fastapi import (
    APIRouter,
    HTTPException,
    status,
)

from app.services.document_service import (
    DocumentService,
)


router = APIRouter(
    prefix="/documents",
    tags=["documents"],
)

UPLOAD_DIRECTORY = Path("uploaded_files")


@router.get("")
def list_documents() -> dict:
    """
    List documents owned by the current local-development user.

    Authentication will later replace user_id=None with the
    authenticated user's ID.
    """
    documents = (
        DocumentService.list_documents(
            user_id=None,
        )
    )

    return {
        "documents": documents,
        "count": len(documents),
    }


@router.get("/{document_id}")
def get_document(
    document_id: str,
) -> dict:
    document = (
        DocumentService.get_document(
            document_id=document_id,
            user_id=None,
        )
    )

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    return document


@router.delete("/{document_id}")
def delete_document(
    document_id: str,
) -> dict:
    try:
        result = (
            DocumentService.delete_document(
                document_id=document_id,
                upload_directory=(
                    UPLOAD_DIRECTORY
                ),
                user_id=None,
            )
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "The document has invalid stored-file "
                "metadata."
            ),
        ) from exc

    except RuntimeError as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    return result
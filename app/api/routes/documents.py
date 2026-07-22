from pathlib import Path

from fastapi import (
    APIRouter,
    HTTPException,
    status,
)

from app.api.dependencies.auth import (
    CurrentUser,
)
from app.services.document_service import (
    DocumentService,
)


router = APIRouter(
    prefix="/documents",
    tags=["documents"],
)

UPLOAD_DIRECTORY = Path(
    "uploaded_files"
)


@router.get(
    "",
    summary="List the authenticated user's documents",
)
def list_documents(
    current_user: CurrentUser,
) -> dict:
    documents = (
        DocumentService.list_documents(
            user_id=current_user.user_id,
        )
    )

    return {
        "documents": documents,
        "count": len(documents),
    }


@router.get(
    "/{document_id}",
    summary="Get one owned document",
)
def get_document(
    document_id: str,
    current_user: CurrentUser,
) -> dict:
    document = (
        DocumentService.get_document(
            document_id=document_id,
            user_id=current_user.user_id,
        )
    )

    if document is None:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail="Document not found.",
        )

    return document


@router.delete(
    "/{document_id}",
    summary="Permanently delete one owned document",
)
def delete_document(
    document_id: str,
    current_user: CurrentUser,
) -> dict:
    try:
        result = (
            DocumentService.delete_document(
                document_id=document_id,
                upload_directory=(
                    UPLOAD_DIRECTORY
                ),
                user_id=(
                    current_user.user_id
                ),
            )
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "The document has invalid "
                "stored-file metadata."
            ),
        ) from exc

    except RuntimeError as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=str(exc),
        ) from exc

    if result is None:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail="Document not found.",
        )

    return result
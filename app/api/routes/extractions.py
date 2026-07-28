from fastapi import (
    APIRouter,
    HTTPException,
    status,
)

from app.api.dependencies.auth import (
    CurrentUser,
)
from app.schemas.extraction_api import (
    ExtractionDeleteResponse,
    ExtractionGenerateRequest,
    ExtractionGenerateResponse,
)
from app.schemas.extraction_persistence import (
    PersistedMedicalExtraction,
)
from app.services.medical_extraction_persistence_service import (
    MedicalExtractionPersistenceError,
    MedicalExtractionPersistenceNotFoundError,
    MedicalExtractionPersistenceService,
)
from app.services.medical_extraction_service import (
    MedicalExtractionContentTooLargeError,
    MedicalExtractionError,
    MedicalExtractionNotFoundError,
    MedicalExtractionService,
    MedicalExtractionValidationError,
)


router = APIRouter(
    prefix="/documents",
    tags=["extractions"],
)


@router.post(
    "/{document_id}/extract",
    response_model=(
        ExtractionGenerateResponse
    ),
    summary=(
        "Generate or retrieve a structured "
        "medical extraction"
    ),
)
def generate_document_extraction(
    document_id: str,
    request: ExtractionGenerateRequest,
    current_user: CurrentUser,
) -> ExtractionGenerateResponse:
    cleaned_document_id = (
        document_id.strip()
    )

    if not cleaned_document_id:
        raise HTTPException(
            status_code=(
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ),
            detail=(
                "A valid document ID is required."
            ),
        )

    try:
        existing_extraction = (
            MedicalExtractionPersistenceService
            .get(
                document_id=(
                    cleaned_document_id
                ),
                user_id=(
                    current_user.user_id
                ),
            )
        )

        if (
            existing_extraction is not None
            and not request.replace_existing
        ):
            return (
                ExtractionGenerateResponse(
                    cached=True,
                    replaced=False,
                    message=(
                        "The previously generated "
                        "structured extraction was "
                        "returned."
                    ),
                    result=(
                        existing_extraction
                    ),
                )
            )

        extraction = (
            MedicalExtractionService.extract(
                document_id=(
                    cleaned_document_id
                ),
                user_id=(
                    current_user.user_id
                ),
            )
        )

        persisted_extraction = (
            MedicalExtractionPersistenceService
            .save(
                extraction=extraction,
                user_id=(
                    current_user.user_id
                ),
            )
        )

        was_replaced = (
            existing_extraction is not None
        )

        return ExtractionGenerateResponse(
            cached=False,
            replaced=was_replaced,
            message=(
                "The structured extraction was "
                "regenerated and replaced."
                if was_replaced
                else (
                    "The structured extraction "
                    "was generated and saved."
                )
            ),
            result=persisted_extraction,
        )

    except (
        MedicalExtractionNotFoundError,
        MedicalExtractionPersistenceNotFoundError,
    ) as exc:
        # Do not reveal whether this document
        # belongs to another account.
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail="Document not found.",
        ) from exc

    except (
        MedicalExtractionContentTooLargeError
    ) as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
            ),
            detail=(
                "The document is too large for "
                "the current structured "
                "extraction pipeline."
            ),
        ) from exc

    except (
        MedicalExtractionValidationError
    ) as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ),
            detail=(
                "The document could not be "
                "converted into a valid "
                "structured extraction."
            ),
        ) from exc

    except MedicalExtractionError as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_502_BAD_GATEWAY
            ),
            detail=(
                "The structured extraction "
                "service is currently "
                "unavailable."
            ),
        ) from exc

    except (
        MedicalExtractionPersistenceError
    ) as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "The structured extraction "
                "could not be stored."
            ),
        ) from exc


@router.get(
    "/{document_id}/extraction",
    response_model=(
        PersistedMedicalExtraction
    ),
    summary=(
        "Retrieve a stored structured "
        "medical extraction"
    ),
)
def get_document_extraction(
    document_id: str,
    current_user: CurrentUser,
) -> PersistedMedicalExtraction:
    cleaned_document_id = (
        document_id.strip()
    )

    if not cleaned_document_id:
        raise HTTPException(
            status_code=(
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ),
            detail=(
                "A valid document ID is required."
            ),
        )

    try:
        extraction = (
            MedicalExtractionPersistenceService
            .get(
                document_id=(
                    cleaned_document_id
                ),
                user_id=(
                    current_user.user_id
                ),
            )
        )

    except (
        MedicalExtractionPersistenceError
    ) as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "The stored extraction could "
                "not be loaded."
            ),
        ) from exc

    if extraction is None:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=(
                "Structured extraction "
                "not found."
            ),
        )

    return extraction


@router.delete(
    "/{document_id}/extraction",
    response_model=(
        ExtractionDeleteResponse
    ),
    summary=(
        "Delete a stored structured medical "
        "extraction"
    ),
)
def delete_document_extraction(
    document_id: str,
    current_user: CurrentUser,
) -> ExtractionDeleteResponse:
    cleaned_document_id = (
        document_id.strip()
    )

    if not cleaned_document_id:
        raise HTTPException(
            status_code=(
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ),
            detail=(
                "A valid document ID is required."
            ),
        )

    try:
        deleted = (
            MedicalExtractionPersistenceService
            .delete(
                document_id=(
                    cleaned_document_id
                ),
                user_id=(
                    current_user.user_id
                ),
            )
        )

    except (
        MedicalExtractionPersistenceError
    ) as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "The stored extraction could "
                "not be deleted."
            ),
        ) from exc

    if not deleted:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=(
                "Structured extraction "
                "not found."
            ),
        )

    return ExtractionDeleteResponse(
        document_id=cleaned_document_id,
        deleted=True,
        message=(
            "The stored structured extraction "
            "was deleted. The original document "
            "was not deleted."
        ),
    )
import logging

from fastapi import (
    APIRouter,
    HTTPException,
    status,
)

from app.api.dependencies.auth import (
    CurrentUser,
)
from app.schemas.intelligence_api import (
    IntelligenceCompareRequest,
    IntelligenceCompareResponse,
    IntelligenceDeleteResponse,
    IntelligenceGenerateRequest,
    IntelligenceGenerateResponse,
    IntelligenceTimelineRequest,
    IntelligenceTimelineResponse,
)
from app.schemas.intelligence_persistence import (
    PersistedMedicalIntelligence,
)
from app.services.document_service import (
    DocumentService,
)
from app.services.medical_extraction_persistence_service import (
    MedicalExtractionPersistenceError,
)
from app.services.medical_intelligence_persistence_service import (
    MedicalIntelligencePersistenceError,
    MedicalIntelligencePersistenceService,
)
from app.services.medical_intelligence_service import (
    MedicalIntelligenceError,
    MedicalIntelligenceService,
)


logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["intelligence"],
)


def _clean_document_id(
    document_id: str,
) -> str:
    cleaned = document_id.strip()

    if not cleaned:
        raise HTTPException(
            status_code=(
                status.HTTP_422_UNPROCESSABLE_CONTENT
            ),
            detail=(
                "A valid document ID is required."
            ),
        )

    return cleaned


def _clean_document_ids(
    document_ids: list[str],
) -> list[str]:
    cleaned: list[str] = []

    for document_id in document_ids:
        value = document_id.strip()

        if (
            value
            and value not in cleaned
        ):
            cleaned.append(value)

    return cleaned


def _verify_owned_documents(
    document_ids: list[str],
    user_id: str,
) -> None:
    existing_ids = (
        DocumentService
        .get_existing_document_ids(
            document_ids=document_ids,
            user_id=user_id,
        )
    )

    if len(existing_ids) != len(
        document_ids
    ):
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=(
                "One or more selected "
                "documents were not found."
            ),
        )


@router.post(
    "/documents/{document_id}/intelligence",
    response_model=(
        IntelligenceGenerateResponse
    ),
    summary=(
        "Generate safe medical intelligence "
        "for an owned document"
    ),
)
def generate_document_intelligence(
    document_id: str,
    request: IntelligenceGenerateRequest,
    current_user: CurrentUser,
) -> IntelligenceGenerateResponse:
    cleaned_document_id = (
        _clean_document_id(
            document_id
        )
    )

    _verify_owned_documents(
        [
            cleaned_document_id,
        ],
        current_user.user_id,
    )

    try:
        (
            extraction,
            extraction_generated,
        ) = (
            MedicalIntelligenceService
            .get_or_generate_extraction(
                document_id=(
                    cleaned_document_id
                ),
                user_id=(
                    current_user.user_id
                ),
            )
        )

        existing = (
            MedicalIntelligencePersistenceService
            .get(
                document_id=(
                    cleaned_document_id
                ),
                user_id=(
                    current_user.user_id
                ),
            )
        )

        is_current = (
            existing is not None
            and (
                existing
                .source_extraction_id
                == extraction.extraction_id
            )
            and (
                existing
                .source_extraction_updated_at
                == extraction.updated_at
            )
        )

        if (
            existing is not None
            and is_current
            and not request.replace_existing
        ):
            return (
                IntelligenceGenerateResponse(
                    cached=True,
                    replaced=False,
                    extraction_generated=(
                        extraction_generated
                    ),
                    message=(
                        "The previously generated "
                        "medical intelligence was "
                        "returned."
                    ),
                    result=existing,
                )
            )

        intelligence = (
            MedicalIntelligenceService
            .build(
                extraction
            )
        )

        persisted = (
            MedicalIntelligencePersistenceService
            .save(
                intelligence=intelligence,
                user_id=(
                    current_user.user_id
                ),
            )
        )

        return IntelligenceGenerateResponse(
            cached=False,
            replaced=(
                existing is not None
            ),
            extraction_generated=(
                extraction_generated
            ),
            message=(
                "Medical intelligence was "
                "generated and stored."
                if existing is None
                else (
                    "Medical intelligence was "
                    "regenerated from the current "
                    "structured extraction."
                )
            ),
            result=persisted,
        )

    except (
        MedicalIntelligenceError,
        MedicalExtractionPersistenceError,
    ) as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_502_BAD_GATEWAY
            ),
            detail=(
                "Medical intelligence could "
                "not be generated."
            ),
        ) from exc

    except (
        MedicalIntelligencePersistenceError
    ) as exc:
        logger.exception(
            (
                "intelligence_persistence_failed "
                "user_id=%s document_id=%s"
            ),
            current_user.user_id,
            cleaned_document_id,
        )

        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "Medical intelligence could "
                "not be stored."
            ),
        ) from exc

    except Exception as exc:
        logger.exception(
            (
                "intelligence_generation_failed "
                "user_id=%s document_id=%s"
            ),
            current_user.user_id,
            cleaned_document_id,
        )

        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "Medical intelligence could "
                "not be generated."
            ),
        ) from exc


@router.get(
    "/documents/{document_id}/intelligence",
    response_model=(
        PersistedMedicalIntelligence
    ),
    summary=(
        "Retrieve stored medical intelligence"
    ),
)
def get_document_intelligence(
    document_id: str,
    current_user: CurrentUser,
) -> PersistedMedicalIntelligence:
    cleaned_document_id = (
        _clean_document_id(
            document_id
        )
    )

    _verify_owned_documents(
        [
            cleaned_document_id,
        ],
        current_user.user_id,
    )

    try:
        intelligence = (
            MedicalIntelligencePersistenceService
            .get(
                document_id=(
                    cleaned_document_id
                ),
                user_id=(
                    current_user.user_id
                ),
            )
        )

        if intelligence is None:
            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail=(
                    "Medical intelligence "
                    "not found."
                ),
            )

        extraction = (
            MedicalIntelligenceService
            .get_or_generate_extraction(
                document_id=(
                    cleaned_document_id
                ),
                user_id=(
                    current_user.user_id
                ),
            )[0]
        )

        if (
            intelligence
            .source_extraction_id
            != extraction.extraction_id
            or (
                intelligence
                .source_extraction_updated_at
                != extraction.updated_at
            )
        ):
            raise HTTPException(
                status_code=(
                    status.HTTP_409_CONFLICT
                ),
                detail=(
                    "Stored medical intelligence "
                    "is outdated because the "
                    "structured extraction changed. "
                    "Regenerate intelligence."
                ),
            )

        return intelligence

    except HTTPException:
        raise

    except (
        MedicalIntelligencePersistenceError,
        MedicalExtractionPersistenceError,
    ) as exc:
        logger.exception(
            (
                "intelligence_load_failed "
                "user_id=%s document_id=%s"
            ),
            current_user.user_id,
            cleaned_document_id,
        )

        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "Stored medical intelligence "
                "could not be loaded."
            ),
        ) from exc


@router.delete(
    "/documents/{document_id}/intelligence",
    response_model=(
        IntelligenceDeleteResponse
    ),
    summary=(
        "Delete stored medical intelligence"
    ),
)
def delete_document_intelligence(
    document_id: str,
    current_user: CurrentUser,
) -> IntelligenceDeleteResponse:
    cleaned_document_id = (
        _clean_document_id(
            document_id
        )
    )

    try:
        deleted = (
            MedicalIntelligencePersistenceService
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
        MedicalIntelligencePersistenceError
    ) as exc:
        logger.exception(
            (
                "intelligence_delete_failed "
                "user_id=%s document_id=%s"
            ),
            current_user.user_id,
            cleaned_document_id,
        )

        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "Stored medical intelligence "
                "could not be deleted."
            ),
        ) from exc

    if not deleted:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=(
                "Medical intelligence "
                "not found."
            ),
        )

    return IntelligenceDeleteResponse(
        document_id=cleaned_document_id,
        deleted=True,
        message=(
            "Stored medical intelligence was "
            "deleted. The original document and "
            "structured extraction were not deleted."
        ),
    )


@router.post(
    "/intelligence/timeline",
    response_model=(
        IntelligenceTimelineResponse
    ),
    summary=(
        "Build a longitudinal timeline "
        "from selected owned documents"
    ),
)
def build_intelligence_timeline(
    request: IntelligenceTimelineRequest,
    current_user: CurrentUser,
) -> IntelligenceTimelineResponse:
    document_ids = (
        _clean_document_ids(
            request.document_ids
        )
    )

    if not document_ids:
        raise HTTPException(
            status_code=(
                status.HTTP_422_UNPROCESSABLE_CONTENT
            ),
            detail=(
                "At least one document "
                "must be selected."
            ),
        )

    _verify_owned_documents(
        document_ids,
        current_user.user_id,
    )

    try:
        return (
            MedicalIntelligenceService
            .timeline(
                document_ids=(
                    document_ids
                ),
                user_id=(
                    current_user.user_id
                ),
            )
        )

    except Exception as exc:
        logger.exception(
            (
                "intelligence_timeline_failed "
                "user_id=%s selected_count=%s"
            ),
            current_user.user_id,
            len(document_ids),
        )

        raise HTTPException(
            status_code=(
                status.HTTP_503_SERVICE_UNAVAILABLE
            ),
            detail=(
                "The medical timeline could "
                "not be generated."
            ),
        ) from exc


@router.post(
    "/intelligence/compare",
    response_model=(
        IntelligenceCompareResponse
    ),
    summary=(
        "Compare documented medical facts "
        "across selected owned documents"
    ),
)
def compare_intelligence_documents(
    request: IntelligenceCompareRequest,
    current_user: CurrentUser,
) -> IntelligenceCompareResponse:
    document_ids = (
        _clean_document_ids(
            request.document_ids
        )
    )

    if len(document_ids) < 2:
        raise HTTPException(
            status_code=(
                status.HTTP_422_UNPROCESSABLE_CONTENT
            ),
            detail=(
                "Select at least two unique "
                "documents for comparison."
            ),
        )

    _verify_owned_documents(
        document_ids,
        current_user.user_id,
    )

    try:
        return (
            MedicalIntelligenceService
            .compare(
                document_ids=(
                    document_ids
                ),
                user_id=(
                    current_user.user_id
                ),
            )
        )

    except Exception as exc:
        logger.exception(
            (
                "intelligence_compare_failed "
                "user_id=%s selected_count=%s"
            ),
            current_user.user_id,
            len(document_ids),
        )

        raise HTTPException(
            status_code=(
                status.HTTP_503_SERVICE_UNAVAILABLE
            ),
            detail=(
                "The selected medical records "
                "could not be compared."
            ),
        ) from exc
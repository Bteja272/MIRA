import logging

import httpx
from fastapi import (
    APIRouter,
    HTTPException,
    status,
)
from sqlalchemy import text

from app.core.config import settings
from app.db.session import SessionLocal
from app.schemas.health import (
    HealthResponse,
    ReadinessResponse,
)


logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["health"],
)


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Check API liveness",
)
def health_check() -> HealthResponse:
    return HealthResponse(
        status="ok",
        application=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
    )


@router.get(
    "/health/ready",
    response_model=ReadinessResponse,
    summary="Check database and LLM readiness",
)
def readiness_check() -> ReadinessResponse:
    database_status = "ok"
    llm_status = "ok"

    db = SessionLocal()

    try:
        db.execute(
            text("SELECT 1")
        )

    except Exception:
        database_status = "unavailable"

        logger.exception(
            "readiness_database_check_failed"
        )

    finally:
        db.close()

    try:
        response = httpx.get(
            (
                settings.ollama_base_url.rstrip("/")
                + "/api/tags"
            ),
            timeout=3.0,
        )

        response.raise_for_status()

    except Exception:
        llm_status = "unavailable"

        logger.warning(
            "readiness_llm_check_failed",
            exc_info=True,
        )

    if (
        database_status != "ok"
        or llm_status != "ok"
    ):
        raise HTTPException(
            status_code=(
                status.HTTP_503_SERVICE_UNAVAILABLE
            ),
            detail={
                "status": "not_ready",
                "database": database_status,
                "llm": llm_status,
            },
        )

    return ReadinessResponse(
        status="ready",
        database="ok",
        llm="ok",
    )
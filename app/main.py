from fastapi import FastAPI

from app.api.routes.documents import (
    router as documents_router,
)
from app.api.routes.health import (
    router as health_router,
)
from app.api.routes.ingest import (
    router as ingest_router,
)
from app.api.routes.query import (
    router as query_router,
)
from app.core.config import settings


OPENAPI_TAGS = [
    {
        "name": "health",
        "description": (
            "Application and dependency health checks."
        ),
    },
    {
        "name": "ingestion",
        "description": (
            "Upload, extract, classify, chunk, embed, "
            "and index medical documents."
        ),
    },
    {
        "name": "query",
        "description": (
            "Ask grounded questions about one or more "
            "selected medical documents."
        ),
    },
    {
        "name": "documents",
        "description": (
            "List, inspect, and permanently delete "
            "uploaded documents."
        ),
    },
]


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "MIRA is a safety-oriented medical-document assistant "
        "for private document ingestion, retrieval, "
        "summarization, comparison, and educational explanation. "
        "The current system is intended for development and "
        "testing and is not a clinical decision-making system."
    ),
    openapi_tags=OPENAPI_TAGS,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


app.include_router(
    health_router
)

app.include_router(
    ingest_router
)

app.include_router(
    query_router
)

app.include_router(
    documents_router
)


@app.get(
    "/",
    tags=["health"],
    summary="API information",
)
def root() -> dict:
    return {
        "message": (
            f"{settings.app_name} API is running"
        ),
        "version": settings.app_version,
        "environment": settings.environment,
        "documentation": "/docs",
        "openapi_schema": "/openapi.json",
    }
from fastapi import (
    FastAPI,
    Request,
)
from fastapi.middleware.cors import (
    CORSMiddleware,
)

from app.api.routes.auth import (
    router as auth_router,
)
from app.api.routes.documents import (
    router as documents_router,
)
from app.api.routes.extractions import (
    router as extractions_router,
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
from app.core.notices import (
    DEVELOPMENT_PRIVACY_NOTICE,
)


OPENAPI_TAGS = [
    {
        "name": "health",
        "description": (
            "Application liveness and dependency "
            "readiness checks."
        ),
    },
    {
        "name": "authentication",
        "description": (
            "Public account registration, login, "
            "and authenticated account information."
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
    {
        "name": "extractions",
        "description": (
            "Generate, retrieve, replace, and delete "
            "structured medical extractions."
        ),
    },
]


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "MIRA is a safety-oriented medical-document assistant "
        "for document ingestion, retrieval, summarization, "
        "comparison, and educational explanation.\n\n"
        f"**Development notice:** "
        f"{DEVELOPMENT_PRIVACY_NOTICE}"
    ),
    openapi_tags=OPENAPI_TAGS,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=(
        settings.cors_allowed_origins
    ),
    allow_credentials=(
        settings.cors_allow_credentials
    ),
    allow_methods=[
        "GET",
        "POST",
        "DELETE",
        "OPTIONS",
    ],
    allow_headers=[
        "Authorization",
        "Content-Type",
    ],
)


@app.middleware("http")
async def add_security_headers(
    request: Request,
    call_next,
):
    response = await call_next(request)

    response.headers.setdefault(
        "Cache-Control",
        "no-store",
    )

    response.headers.setdefault(
        "X-Content-Type-Options",
        "nosniff",
    )

    response.headers.setdefault(
        "X-Frame-Options",
        "DENY",
    )

    response.headers.setdefault(
        "Referrer-Policy",
        "no-referrer",
    )

    return response


app.include_router(health_router)
app.include_router(auth_router)
app.include_router(ingest_router)
app.include_router(query_router)
app.include_router(documents_router)
app.include_router(extractions_router)


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
        "development_notice": (
            DEVELOPMENT_PRIVACY_NOTICE
        ),
    }
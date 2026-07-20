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


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "MIRA provides private medical-document retrieval, "
        "summarization, and educational explanations."
    ),
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


@app.get("/")
def root() -> dict:
    return {
        "message": (
            f"{settings.app_name} API is running"
        ),
        "version": settings.app_version,
        "environment": settings.environment,
    }
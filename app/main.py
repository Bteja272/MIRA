import re

from fastapi import (
    FastAPI,
    Request,
)
from fastapi.middleware.cors import (
    CORSMiddleware,
)
from fastapi.responses import (
    JSONResponse,
)
from starlette.middleware.trustedhost import (
    TrustedHostMiddleware,
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
from app.core.csrf import (
    csrf_is_valid,
)
from app.core.notices import (
    DEVELOPMENT_PRIVACY_NOTICE,
)
from app.core.rate_limit import (
    get_rate_limit_policy,
    rate_limiter,
)
from app.core.security_config import (
    security_settings,
)
from app.services.audit_service import (
    AuditService,
)
from app.api.routes.intelligence import (
    router as intelligence_router,
)
from app.api.routes.conversations import (
    router as conversations_router,
)

OPENAPI_TAGS = [
    {
        "name": "health",
        "description": (
            "Application health checks."
        ),
    },
    {
        "name": "authentication",
        "description": (
            "Account authentication "
            "and session management."
        ),
    },
    {
        "name": "ingestion",
        "description": (
            "Medical document ingestion."
        ),
    },
    {
        "name": "documents",
        "description": (
            "Authenticated document "
            "management."
        ),
    },
    {
        "name": "query",
        "description": (
            "MIRA medical-document "
            "query operations."
        ),
    },
    {
        "name": "extractions",
        "description": (
            "Structured medical "
            "extraction operations."
        ),
    },
    {
        "name": "intelligence",
        "description": (
            "Safe medical document understanding, "
            "normalization, timeline, and "
            "longitudinal comparison."
        ),
    },
    {
        "name": "conversations",
        "description": (
            "Authenticated bounded "
            "conversation-memory operations."
        ),
    },
]


def validate_production_security():
    environment = (
        settings.environment
        .strip()
        .lower()
    )

    if environment not in {
        "production",
        "prod",
    }:
        return

    secret = (
        settings.jwt_secret_key
        .get_secret_value()
    )

    weak_values = {
        "",
        "secret",
        "secret_shhh",
        "changeme",
        "change-me",
        "development",
    }

    if (
        len(secret) < 32
        or secret.strip().lower()
        in weak_values
    ):
        raise RuntimeError(
            "Production JWT_SECRET_KEY "
            "must be a strong secret of "
            "at least 32 characters."
        )

    if not (
        security_settings
        .cookie_secure
    ):
        raise RuntimeError(
            "Production requires "
            "COOKIE_SECURE=true."
        )

    if not (
        security_settings
        .csrf_enabled
    ):
        raise RuntimeError(
            "Production requires "
            "CSRF_ENABLED=true."
        )

    if "*" in (
        security_settings
        .trusted_hosts
    ):
        raise RuntimeError(
            "Wildcard TRUSTED_HOSTS are "
            "not allowed in production."
        )

    for origin in (
        settings
        .cors_allowed_origins
    ):
        if not origin.startswith(
            "https://"
        ):
            raise RuntimeError(
                "Production CORS origins "
                "must use HTTPS."
            )


validate_production_security()


docs_enabled = (
    security_settings
    .expose_api_docs
)


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    openapi_tags=OPENAPI_TAGS,
    docs_url=(
        "/docs"
        if docs_enabled
        else None
    ),
    redoc_url=(
        "/redoc"
        if docs_enabled
        else None
    ),
    openapi_url=(
        "/openapi.json"
        if docs_enabled
        else None
    ),
)


app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=(
        security_settings
        .trusted_hosts
    ),
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=(
        settings
        .cors_allowed_origins
    ),
    allow_credentials=(
        settings
        .cors_allow_credentials
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
        "X-CSRF-Token",
    ],
)


def _audit_metadata(
    request: Request,
) -> tuple[
    str | None,
    str | None,
    str | None,
]:
    path = request.url.path
    method = request.method.upper()

    if (
        path == "/auth/register"
        and method == "POST"
    ):
        return (
            "auth_register",
            "user",
            None,
        )

    if (
        path == "/auth/login"
        and method == "POST"
    ):
        return (
            "auth_login",
            "session",
            None,
        )

    if (
        path == "/auth/refresh"
        and method == "POST"
    ):
        return (
            "auth_refresh",
            "session",
            None,
        )

    if (
        path == "/auth/logout"
        and method == "POST"
    ):
        return (
            "auth_logout",
            "session",
            None,
        )

    if (
        path == "/ingest"
        and method == "POST"
    ):
        return (
            "document_upload",
            "document",
            None,
        )

    if (
        path == "/query"
        and method == "POST"
    ):
        return (
            "query_execute",
            "query",
            None,
        )

    extraction_match = re.fullmatch(
        r"/documents/"
        r"([^/]+)/extract",
        path,
    )

    if (
        extraction_match
        and method == "POST"
    ):
        return (
            "extraction_generate",
            "document",
            extraction_match.group(1),
        )

    stored_extraction_match = (
        re.fullmatch(
            r"/documents/"
            r"([^/]+)/extraction",
            path,
        )
    )

    if (
        stored_extraction_match
        and method == "DELETE"
    ):
        return (
            "extraction_delete",
            "document",
            stored_extraction_match
            .group(1),
        )
    
    intelligence_match = (
        re.fullmatch(
            r"/documents/"
            r"([^/]+)/intelligence",
            path,
        )
    )

    if intelligence_match:
        if method == "POST":
            return (
                "intelligence_generate",
                "document",
                intelligence_match.group(1),
            )

        if method == "GET":
            return (
                "intelligence_read",
                "document",
                intelligence_match.group(1),
            )

        if method == "DELETE":
            return (
                "intelligence_delete",
                "document",
                intelligence_match.group(1),
            )

    if (
        path == "/intelligence/timeline"
        and method == "POST"
    ):
        return (
            "intelligence_timeline",
            "medical_intelligence",
            None,
        )

    if (
        path == "/intelligence/compare"
        and method == "POST"
    ):
        return (
            "intelligence_compare",
            "medical_intelligence",
            None,
        )

    document_match = (
        re.fullmatch(
            r"/documents/([^/]+)",
            path,
        )
    )

    if (
        document_match
        and method == "DELETE"
    ):
        return (
            "document_delete",
            "document",
            document_match.group(1),
        )
        conversation_match = (
            re.fullmatch(
                r"/conversations/([^/]+)",
                path,
            )
        )

        if (
            path == "/conversations"
            and method == "GET"
        ):
            return (
                "conversation_list",
                "conversation",
                None,
            )

        if (
            conversation_match
            and method == "GET"
        ):
            return (
                "conversation_read",
                "conversation",
                conversation_match.group(1),
            )

        if (
            conversation_match
            and method == "DELETE"
        ):
            return (
                "conversation_delete",
                "conversation",
                conversation_match.group(1),
            )
    return (
        None,
        None,
        None,
    )


@app.middleware("http")
async def security_middleware(
    request: Request,
    call_next,
):
    if (
        security_settings
        .rate_limit_enabled
        and request.method.upper()
        != "OPTIONS"
    ):
        (
            key,
            limit,
            window_seconds,
        ) = get_rate_limit_policy(
            request
        )

        retry_after = (
            rate_limiter.check(
                key=key,
                limit=limit,
                window_seconds=(
                    window_seconds
                ),
            )
        )

        if retry_after:
            return JSONResponse(
                status_code=429,
                content={
                    "detail": (
                        "Too many requests. "
                        "Try again later."
                    )
                },
                headers={
                    "Retry-After": str(
                        retry_after
                    ),
                },
            )

    if not csrf_is_valid(
        request
    ):
        return JSONResponse(
            status_code=403,
            content={
                "detail": (
                    "CSRF validation failed."
                )
            },
        )

    response = await call_next(
        request
    )

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

    response.headers.setdefault(
        "Permissions-Policy",
        (
            "camera=(), "
            "microphone=(), "
            "geolocation=()"
        ),
    )

    if (
        docs_enabled
        and request.url.path
        in {
            "/docs",
            "/redoc",
            "/openapi.json",
        }
    ):
        response.headers.setdefault(
            "Content-Security-Policy",
            (
                "default-src 'self' https:; "
                "script-src 'self' https: 'unsafe-inline'; "
                "style-src 'self' https: 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' https: data:; "
                "frame-ancestors 'none'"
            ),
        )
    else:
        response.headers.setdefault(
            "Content-Security-Policy",
            (
                "default-src 'none'; "
                "frame-ancestors 'none'"
            ),
        )

    if (
        security_settings
        .hsts_enabled
        and request.url.scheme
        == "https"
    ):
        response.headers.setdefault(
            "Strict-Transport-Security",
            (
                "max-age=31536000; "
                "includeSubDomains"
            ),
        )

    (
        event_type,
        resource_type,
        resource_id,
    ) = _audit_metadata(
        request
    )

    if event_type is not None:
        status_code = (
            response.status_code
        )

        if (
            200
            <= status_code
            < 400
        ):
            outcome = "success"
        elif status_code == 404:
            outcome = "not_found"
        else:
            outcome = "failure"

        AuditService.record(
            event_type=event_type,
            outcome=outcome,
            user_id=getattr(
                request.state,
                "user_id",
                None,
            ),
            resource_type=(
                resource_type
            ),
            resource_id=resource_id,
            details={
                "status_code": (
                    status_code
                ),
            },
        )

    return response


app.include_router(
    health_router
)

app.include_router(
    auth_router
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

app.include_router(
    extractions_router
)
app.include_router(
    intelligence_router
)
app.include_router(
    conversations_router
)

@app.get("/")
def root():
    return {
        "app": settings.app_name,
        "version": (
            settings.app_version
        ),
        "environment": (
            settings.environment
        ),
        "documentation": (
            "/docs"
            if docs_enabled
            else None
        ),
        "development_notice": (
            DEVELOPMENT_PRIVACY_NOTICE
        ),
    }
from fastapi import APIRouter
from backend.app.schemas.health import (
    HealthCheckResponse,
    DatabaseHealthResponse,
    ProviderHealthResponse,
    GeminiProviderStatus,
    SupabaseProviderStatus,
)
from backend.app.core.database import check_database_connectivity
from backend.app.core.config import settings
from backend.app.services.gemini import gemini_service
from backend.app.services.supabase import supabase_service

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthCheckResponse, summary="Basic process health check")
def basic_health() -> HealthCheckResponse:
    """
    Lightweight process liveness health check per API_SPEC.md.
    Does not expose sensitive credentials or infrastructure details.
    """
    return HealthCheckResponse(status="ok")


@router.get("/health/db", response_model=DatabaseHealthResponse, summary="Database connectivity check")
def database_health() -> DatabaseHealthResponse:
    """
    Separate database connectivity check.
    Tests PostgreSQL/Supabase connectivity using SELECT 1.
    """
    db_status = check_database_connectivity()
    return DatabaseHealthResponse(
        status=db_status["status"],
        connected=db_status["connected"],
        message=db_status["message"],
        database_url_configured=settings.is_database_configured,
    )


@router.get("/health/providers", response_model=ProviderHealthResponse, summary="External provider status")
def providers_health() -> ProviderHealthResponse:
    """
    External provider health checks (Gemini, Supabase).
    Kept separate from basic application health so provider outages
    or unconfigured keys do not bring down process liveness.
    """
    gemini_configured = gemini_service.is_configured
    supabase_configured = supabase_service.is_configured

    gemini_status = GeminiProviderStatus(
        configured=gemini_configured,
        generation_model=settings.GEMINI_GENERATION_MODEL,
        embedding_model=settings.GEMINI_EMBEDDING_MODEL,
        embedding_dimensions=settings.EMBEDDING_DIMENSIONS,
        status="configured" if gemini_configured else "missing_api_key",
        details="Key present in environment" if gemini_configured else "GEMINI_API_KEY is not set"
    )

    supabase_status = SupabaseProviderStatus(
        configured=supabase_configured,
        status="configured" if supabase_configured else "missing_credentials",
        storage_bucket=settings.SUPABASE_STORAGE_BUCKET
    )

    overall = "ok" if (gemini_configured and supabase_configured) else "partially_configured"

    return ProviderHealthResponse(
        status=overall,
        gemini=gemini_status,
        supabase=supabase_status,
    )

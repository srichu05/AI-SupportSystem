from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class HealthCheckResponse(BaseModel):
    """Basic process health response matching GET /health in API_SPEC.md."""
    status: str = Field(default="ok", description="Basic health status")


class DatabaseHealthResponse(BaseModel):
    """Database connectivity health check."""
    status: str = Field(..., description="healthy | unhealthy | not_configured")
    connected: bool = Field(..., description="Whether database connection succeeded")
    message: str = Field(..., description="Status description")
    database_url_configured: bool = Field(..., description="Whether DATABASE_URL was provided")


class GeminiProviderStatus(BaseModel):
    configured: bool
    generation_model: str
    embedding_model: str
    embedding_dimensions: int
    status: str
    details: Optional[str] = None


class SupabaseProviderStatus(BaseModel):
    configured: bool
    status: str
    storage_bucket: str


class ProviderHealthResponse(BaseModel):
    """External provider health status (separate from basic app health)."""
    status: str = Field(..., description="overall status of external services")
    gemini: GeminiProviderStatus
    supabase: SupabaseProviderStatus

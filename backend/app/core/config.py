import json
from pathlib import Path
from typing import List, Optional, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    # Server & runtime
    PROJECT_NAME: str = "Intelligent Customer Complaint Response Assistant"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = Field(default="development", description="development | production | testing")
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    LOG_LEVEL: str = "INFO"

    # CORS
    CORS_ORIGINS: Union[List[str], str] = Field(
        default=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173", "http://127.0.0.1:3000"],
        description="Allowed CORS origins"
    )
    CORS_ORIGIN_REGEX: Optional[str] = Field(
        default=r"^https://.*\.vercel\.app$",
        description="Regex pattern for dynamic CORS origins such as Vercel preview and production deployments"
    )

    # Database
    DATABASE_URL: Optional[str] = Field(
        default=None,
        description="PostgreSQL / Supabase connection URL"
    )

    # Supabase Client
    SUPABASE_URL: Optional[str] = Field(default=None, description="Supabase project URL")
    SUPABASE_ANON_KEY: Optional[str] = Field(default=None, description="Supabase anon/public key")
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = Field(default=None, description="Supabase service role secret key")
    SUPABASE_STORAGE_BUCKET: str = Field(default="policy-documents", description="Storage bucket name")

    # Gemini API
    GEMINI_API_KEY: Optional[str] = Field(default=None, description="Google Gemini API key")
    GEMINI_GENERATION_MODEL: str = Field(default="gemini-3.8-flash", description="Model ID for generation")
    GEMINI_EMBEDDING_MODEL: str = Field(default="gemini-embedding-2", description="Model ID for embeddings")
    EMBEDDING_DIMENSIONS: int = Field(default=768, description="Target dimension for embeddings")

    # Clerk Authentication
    CLERK_SECRET_KEY: Optional[str] = Field(default=None, description="Clerk secret key (sk_test_... or sk_live_...)")
    CLERK_PUBLISHABLE_KEY: Optional[str] = Field(default=None, description="Clerk publishable key (pk_test_... or pk_live_...)")
    CLERK_JWT_KEY: Optional[str] = Field(default=None, description="Clerk PEM public key for local JWT verification")
    CLERK_JWKS_URL: Optional[str] = Field(default=None, description="Clerk JWKS URL for key retrieval")
    CLERK_ISSUER: Optional[str] = Field(default=None, description="Expected Clerk token issuer URL")
    CLERK_AUTHORIZED_PARTY: Optional[str] = Field(default=None, description="Expected authorized party (azp) origin")
    AUTH_ENABLED: bool = Field(default=True, description="Enforce Clerk authentication on protected routes")

    # Ingestion & Chunking
    CHUNK_SIZE: int = Field(default=1500, description="Target chunk size in characters (~375 tokens)")
    CHUNK_OVERLAP: int = Field(default=200, description="Chunk overlap in characters (~50 tokens)")
    MAX_UPLOAD_SIZE_BYTES: int = Field(default=20 * 1024 * 1024, description="Maximum upload size in bytes (20MB)")

    # Hybrid Retrieval & RRF
    RETRIEVAL_TOP_K_VECTOR: int = Field(default=10, description="Top candidate chunks from vector search")
    RETRIEVAL_TOP_K_KEYWORD: int = Field(default=10, description="Top candidate chunks from full-text search")
    RETRIEVAL_FINAL_TOP_K: int = Field(default=5, description="Top fused chunks returned to downstream consumer")
    RETRIEVAL_RRF_K: int = Field(default=60, description="Reciprocal Rank Fusion smoothing constant k")

    # Settings configuration
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env", "../../.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: Union[str, List[str]]) -> List[str]:
        if isinstance(value, list):
            return [str(v).strip() for v in value if str(v).strip()]
        if isinstance(value, str):
            val = value.strip()
            if not val:
                return ["*"]
            if val.startswith("[") and val.endswith("]"):
                try:
                    parsed = json.loads(val)
                    if isinstance(parsed, list):
                        return [str(item).strip() for item in parsed if str(item).strip()]
                except json.JSONDecodeError:
                    pass
            # Split comma-separated string
            return [origin.strip() for origin in val.split(",") if origin.strip()]
        return ["*"]

    @field_validator("DATABASE_URL", mode="after")
    @classmethod
    def normalize_database_url(cls, value: Optional[str]) -> Optional[str]:
        if value:
            trimmed = value.strip()
            # SQLAlchemy 1.4+ / 2.0 requires postgresql:// instead of postgres://
            if trimmed.startswith("postgres://"):
                return "postgresql://" + trimmed[len("postgres://"):]
            return trimmed
        return None

    @property
    def is_database_configured(self) -> bool:
        return bool(self.DATABASE_URL and self.DATABASE_URL.strip())

    @property
    def is_gemini_configured(self) -> bool:
        return bool(self.GEMINI_API_KEY and self.GEMINI_API_KEY.strip())

    @property
    def is_supabase_configured(self) -> bool:
        return bool(self.SUPABASE_URL and self.SUPABASE_URL.strip())

    @property
    def is_clerk_configured(self) -> bool:
        return bool(
            (self.CLERK_SECRET_KEY and self.CLERK_SECRET_KEY.strip())
            or (self.CLERK_JWT_KEY and self.CLERK_JWT_KEY.strip())
            or (self.CLERK_JWKS_URL and self.CLERK_JWKS_URL.strip())
            or (self.CLERK_PUBLISHABLE_KEY and self.CLERK_PUBLISHABLE_KEY.strip())
        )

    def masked_database_url(self) -> str:
        """Return database URL with password masked."""
        if not self.DATABASE_URL:
            return "not_configured"
        try:
            # Mask password in URL
            from urllib.parse import urlparse
            parsed = urlparse(self.DATABASE_URL)
            if parsed.password:
                netloc = parsed.netloc.replace(f":{parsed.password}@", ":****@")
                return parsed._replace(netloc=netloc).geturl()
            return self.DATABASE_URL
        except Exception:
            return "configured (masked)"


settings = Settings()

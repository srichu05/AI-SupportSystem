from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.app.core.config import settings
from backend.app.core.logging import setup_logging, get_logger
from backend.app.core.errors import (
    AppException,
    app_exception_handler,
    validation_exception_handler,
    http_exception_handler,
    unhandled_exception_handler,
)
from backend.app.schemas.health import HealthCheckResponse
from backend.app.api.v1.router import api_v1_router
from backend.app.api.v1.endpoints.health import database_health, providers_health

# Initialize structured logging
setup_logging(settings.LOG_LEVEL)
logger = get_logger("complaint_assistant.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    logger.info("Starting %s in %s mode", settings.PROJECT_NAME, settings.ENVIRONMENT)
    logger.info("CORS origins allowed: %s", settings.CORS_ORIGINS)
    logger.info("Database configured: %s", settings.is_database_configured)
    logger.info("Gemini API configured: %s", settings.is_gemini_configured)
    yield
    logger.info("Shutting down %s", settings.PROJECT_NAME)


def create_application() -> FastAPI:
    """FastAPI application factory."""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version="0.1.0",
        description="FastAPI backend for Intelligent Customer Complaint Response Assistant (PS-40)",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # 1. CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 2. Centralized Exception Handlers
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    # 3. Root Health Endpoint (per API_SPEC.md line 22)
    @app.get(
        "/health",
        response_model=HealthCheckResponse,
        tags=["Health"],
        summary="Basic process health check",
    )
    def root_health() -> HealthCheckResponse:
        """Basic process health check returning {'status': 'ok'}."""
        return HealthCheckResponse(status="ok")

    # Additional root health paths for convenience
    app.add_api_route("/health/db", database_health, methods=["GET"], tags=["Health"])
    app.add_api_route("/health/providers", providers_health, methods=["GET"], tags=["Health"])

    # 4. Mount API v1 Modular Router
    app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)

    return app


app = create_application()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host=settings.HOST, port=settings.PORT, reload=True)

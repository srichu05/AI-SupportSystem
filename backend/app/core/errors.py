import logging
from typing import Any, Dict, Optional
from fastapi import Request, HTTPException, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger("complaint_assistant.errors")

HTTP_422 = getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422)


class AppException(Exception):
    """Base application exception following API_SPEC.md error format."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        retryable: bool = False,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.retryable = retryable
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "retryable": self.retryable,
            }
        }


class DatabaseUnavailableException(AppException):
    def __init__(self, message: str = "Database is temporarily unreachable."):
        super().__init__(
            code="DATABASE_UNAVAILABLE",
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            retryable=True,
        )


class DatabaseNotConfiguredException(AppException):
    def __init__(self, message: str = "Database connection has not been configured."):
        super().__init__(
            code="DATABASE_NOT_CONFIGURED",
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            retryable=False,
        )


class ProviderUnavailableException(AppException):
    def __init__(self, provider: str = "Embedding", message: Optional[str] = None):
        code = f"{provider.upper()}_PROVIDER_UNAVAILABLE"
        msg = message or f"{provider} service is temporarily unavailable."
        super().__init__(
            code=code,
            message=msg,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            retryable=True,
        )


class ProviderRateLimitException(AppException):
    def __init__(self, provider: str = "Gemini", message: Optional[str] = None):
        super().__init__(
            code="PROVIDER_RATE_LIMIT",
            message=message or f"{provider} provider rate limit exceeded. Please try again shortly.",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            retryable=True,
        )


class InvalidInputException(AppException):
    def __init__(self, message: str):
        super().__init__(
            code="INVALID_INPUT",
            message=message,
            status_code=HTTP_422,
            retryable=False,
        )


class UnsupportedFileTypeException(AppException):
    def __init__(self, message: str = "Unsupported file type. Only PDF, DOCX, and TXT are accepted."):
        super().__init__(
            code="UNSUPPORTED_FILE_TYPE",
            message=message,
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            retryable=False,
        )


class EmptyDocumentException(AppException):
    def __init__(self, message: str = "Uploaded document contains no extractable text."):
        super().__init__(
            code="EMPTY_DOCUMENT",
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            retryable=False,
        )


class DocumentSizeLimitExceededException(AppException):
    def __init__(self, message: str = "Document exceeds the maximum allowed file size."):
        status_413 = getattr(status, "HTTP_413_CONTENT_TOO_LARGE", getattr(status, "HTTP_413_REQUEST_ENTITY_TOO_LARGE", 413))
        super().__init__(
            code="DOCUMENT_SIZE_EXCEEDED",
            message=message,
            status_code=status_413,
            retryable=False,
        )


class DocumentExtractionException(AppException):
    def __init__(self, message: str = "Failed to parse or extract text from the document."):
        super().__init__(
            code="DOCUMENT_EXTRACTION_FAILURE",
            message=message,
            status_code=HTTP_422,
            retryable=False,
        )


class InvalidModelOutputException(AppException):
    def __init__(self, message: str = "Provider returned invalid or malformed output."):
        super().__init__(
            code="INVALID_MODEL_OUTPUT",
            message=message,
            status_code=status.HTTP_502_BAD_GATEWAY,
            retryable=True,
        )


class PolicyNotIngestedException(AppException):
    def __init__(self, message: str = "The requested policy document has not been ingested."):
        super().__init__(
            code="POLICY_NOT_INGESTED",
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            retryable=False,
        )


class ResourceNotFoundException(AppException):
    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(
            code=f"{resource_type.upper()}_NOT_FOUND",
            message=f"{resource_type.capitalize()} '{resource_id}' was not found.",
            status_code=status.HTTP_404_NOT_FOUND,
            retryable=False,
        )


class InvalidReviewDecisionException(AppException):
    def __init__(self, message: str = "Invalid review decision. Must be approved, rejected, or escalated."):
        super().__init__(
            code="INVALID_REVIEW_DECISION",
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            retryable=False,
        )


class CitationValidationException(AppException):
    def __init__(self, message: str = "One or more cited chunk IDs do not exist in the retrieved evidence set."):
        super().__init__(
            code="CITATION_VALIDATION_FAILURE",
            message=message,
            status_code=HTTP_422,
            retryable=False,
        )


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handle custom application exceptions."""
    logger.warning("Application exception on %s: [%s] %s", request.url.path, exc.code, exc.message)
    return JSONResponse(status_code=exc.status_code, content=exc.to_dict())


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Format Pydantic request validation errors into standard error contract."""
    # Create clean error message without exposing python internal details
    errors = exc.errors()
    msg_parts = []
    for err in errors:
        loc = " -> ".join(str(l) for l in err.get("loc", []))
        msg = err.get("msg", "invalid")
        msg_parts.append(f"{loc}: {msg}" if loc else msg)
    message = "; ".join(msg_parts) if msg_parts else "Invalid request data."

    logger.info("Request validation failed on %s: %s", request.url.path, message)
    return JSONResponse(
        status_code=HTTP_422,
        content={
            "error": {
                "code": "INVALID_INPUT",
                "message": message,
                "retryable": False,
            }
        },
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Format standard FastAPI/Starlette HTTP exceptions into standard error contract."""
    code = "HTTP_ERROR"
    if exc.status_code == status.HTTP_404_NOT_FOUND:
        code = "NOT_FOUND"
    elif exc.status_code == status.HTTP_401_UNAUTHORIZED:
        code = "UNAUTHORIZED"
    elif exc.status_code == status.HTTP_403_FORBIDDEN:
        code = "FORBIDDEN"
    elif exc.status_code == status.HTTP_400_BAD_REQUEST:
        code = "BAD_REQUEST"

    message = str(exc.detail) if exc.detail else "An HTTP error occurred."
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "retryable": False,
            }
        },
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all handler for unexpected internal exceptions. Never leaks secrets or raw tracebacks."""
    logger.exception("Unhandled server exception on %s", request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An internal server error occurred.",
                "retryable": False,
            }
        },
    )

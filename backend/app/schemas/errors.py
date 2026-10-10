from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error description")
    retryable: bool = Field(default=False, description="Whether the request can be retried safely")


class ErrorResponse(BaseModel):
    """Standardized API error response shape matching API_SPEC.md."""
    error: ErrorDetail

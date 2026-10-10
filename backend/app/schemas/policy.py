from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field


class PolicyUploadResponse(BaseModel):
    """Response returned upon policy upload."""
    document_id: str = Field(..., description="Unique UUID of uploaded policy")
    status: str = Field(..., description="Ingestion status: processing | completed | failed")


class PolicyDocumentResponse(BaseModel):
    """Detailed policy document metadata."""
    document_id: str
    source_filename: str
    document_type: str
    version_label: Optional[str] = None
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    status: str
    created_at: datetime

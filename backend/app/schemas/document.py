from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel


class DocumentStatus(StrEnum):
    """Status of document processing."""

    PROCESSING = "PROCESSING"
    READY = "READY"
    FAILED = "FAILED"


class DocumentSummary(BaseModel):
    """Summary of an uploaded document."""

    document_id: str
    document_name: str
    content_sha256: str
    status: DocumentStatus
    error: str | None = None
    created_at: datetime


class DocumentList(BaseModel):
    """Response wrapper for a list of uploaded documents."""

    documents: list[DocumentSummary]


class DocumentUploadResult(BaseModel):
    """Result of a document upload request."""

    accepted: list[str]
    rejected: list[str]

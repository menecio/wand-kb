from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel


class DocumentStatus(StrEnum):
    """Status of document processing."""

    PROCESSING = "PROCESSING"
    READY = "READY"
    FAILED = "FAILED"
    REJECTED = "REJECTED"
    DUPLICATE = "DUPLICATE"


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


class DocumentDeleteResponse(BaseModel):
    """Result of deleting a single document."""

    document_id: str
    deleted: bool


class UploadResultItem(BaseModel):
    """Per-file result of a document upload request."""

    filename: str
    status: DocumentStatus
    document_id: str | None = None
    error: str | None = None


class DocumentUploadResult(BaseModel):
    """Result of a document upload request."""

    results: list[UploadResultItem]

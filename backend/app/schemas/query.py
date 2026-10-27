from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field, model_validator


class ConfidenceLevel(StrEnum):
    """Confidence levels for answer quality."""

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


class ActionType(StrEnum):
    """Types of enrichment actions."""

    UPLOAD_DOCUMENT = "UPLOAD_DOCUMENT"
    QUERY_EXTERNAL_SYSTEM = "QUERY_EXTERNAL_SYSTEM"
    ASK_USER = "ASK_USER"


class Citation(BaseModel):
    """A citation referencing a specific chunk of a document."""

    chunk_id: str
    document_id: str
    document_name: str
    page_start: int | None = None
    page_end: int | None = None
    section: str | None = None
    excerpt: str
    relevance_score: float = Field(ge=0.0, le=1.0)


class EnrichmentSuggestion(BaseModel):
    """A suggestion for enriching the knowledge base."""

    action_type: ActionType
    target: str
    reason: str
    suggested_query: str | None = None


class QueryRequest(BaseModel):
    """Request model for querying the knowledge base."""

    question: str = Field(..., min_length=1, max_length=10000)


class QueryResponse(BaseModel):
    """Response model for knowledge base queries."""

    response_id: str
    answer: str
    confidence: ConfidenceLevel
    is_complete: bool
    missing_info: list[str]
    enrichment_suggestions: list[EnrichmentSuggestion]
    citations: list[Citation]

    @model_validator(mode="after")
    def check_integrity(self) -> QueryResponse:
        # IR-4: INSUFFICIENT_DATA implies incomplete
        if self.confidence == ConfidenceLevel.INSUFFICIENT_DATA and self.is_complete:
            raise ValueError("INSUFFICIENT_DATA confidence requires is_complete=False")

        # IR-3: Completeness implies no material gaps
        if self.is_complete and self.missing_info:
            raise ValueError("is_complete=True requires missing_info to be empty")

        # IR-1: Factual answers require valid citations
        if not self.citations and not (
            self.confidence == ConfidenceLevel.INSUFFICIENT_DATA and not self.is_complete
        ):
            raise ValueError(
                "Empty citations are only allowed when confidence is INSUFFICIENT_DATA "
                "and is_complete is False"
            )

        return self

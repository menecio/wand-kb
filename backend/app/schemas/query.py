from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field, model_validator

from app.schemas.facet import Facet, FacetStatus


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
    facets: list[Facet] = Field(default_factory=list)

    @model_validator(mode="after")
    def check_integrity(self) -> QueryResponse:
        # IR-4: INSUFFICIENT_DATA implies incomplete
        if self.confidence == ConfidenceLevel.INSUFFICIENT_DATA and self.is_complete:
            raise ValueError("INSUFFICIENT_DATA confidence requires is_complete=False")

        # IR-3: Completeness implies no material gaps
        if self.is_complete and self.missing_info:
            raise ValueError("is_complete=True requires missing_info to be empty")

        gap_facet_statuses = {
            FacetStatus.MISSING,
            FacetStatus.UNCERTAIN,
            FacetStatus.CONFLICTING,
        }
        if self.is_complete and any(f.status in gap_facet_statuses for f in self.facets):
            raise ValueError(
                "is_complete=True requires no MISSING/UNCERTAIN/CONFLICTING facets"
            )

        # IR-1: Factual answers require valid citations
        if not self.citations and not (
            self.confidence == ConfidenceLevel.INSUFFICIENT_DATA and not self.is_complete
        ):
            raise ValueError(
                "Empty citations are only allowed when confidence is INSUFFICIENT_DATA "
                "and is_complete is False"
            )

        # IR-2: Answered facets reference citations that are present in the response
        citation_chunk_ids = {c.chunk_id for c in self.citations}
        for facet in self.facets:
            if facet.status == FacetStatus.ANSWERED:
                if not facet.citation_ids:
                    raise ValueError("ANSWERED facets must have at least one citation_id")
                for chunk_id in facet.citation_ids:
                    if chunk_id not in citation_chunk_ids:
                        raise ValueError(
                            f"ANSWERED facet references unknown citation_id {chunk_id}"
                        )

        # IR-6: Enrichment suggestions must reference an identified gap. If a suggestion
        # does not already reference a gap, append a clear reference so the invariant holds.
        gaps = set(self.missing_info)
        for facet in self.facets:
            if facet.associated_gap:
                gaps.add(facet.associated_gap)
        if gaps:
            corrected_suggestions: list[EnrichmentSuggestion] = []
            for suggestion in self.enrichment_suggestions:
                if not any(gap in suggestion.reason for gap in gaps):
                    corrected_suggestions.append(
                        EnrichmentSuggestion(
                            action_type=suggestion.action_type,
                            target=suggestion.target,
                            reason=f"{suggestion.reason} (Gap: {next(iter(gaps))})",
                            suggested_query=suggestion.suggested_query,
                        )
                    )
                else:
                    corrected_suggestions.append(suggestion)
            self.enrichment_suggestions = corrected_suggestions

        return self


class SearchRequest(BaseModel):
    """Request model for semantic search over the knowledge base."""

    query: str = Field(..., min_length=1, max_length=10000)
    top_k: int = Field(default=5, ge=1, le=50)


class SearchResult(BaseModel):
    """A single ranked chunk returned by semantic search."""

    chunk_id: str
    document_id: str
    document_name: str
    section: str | None = None
    excerpt: str
    score: float


class SearchResponse(BaseModel):
    """Response model for semantic search."""

    results: list[SearchResult]

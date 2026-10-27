"""Tests for Pydantic models."""
from datetime import datetime

import pytest
from pydantic import ValidationError

from app.schemas.document import DocumentStatus, DocumentSummary
from app.schemas.facet import Facet, FacetStatus
from app.schemas.query import (
    ActionType,
    Citation,
    EnrichmentSuggestion,
    QueryRequest,
)


def test_query_request_valid():
    """Test valid QueryRequest."""
    request = QueryRequest(question="What is the capital of France?")
    assert request.question == "What is the capital of France?"

def test_query_request_empty_question():
    """Test QueryRequest with empty question raises validation error."""
    with pytest.raises(ValidationError):
        QueryRequest(question="")

def test_citation_valid():
    """Test valid Citation."""
    citation = Citation(
        chunk_id="chunk_123",
        document_id="doc_456",
        document_name="test.pdf",
        page_start=1,
        page_end=2,
        section="Introduction",
        excerpt="This is a test excerpt",
        relevance_score=0.95
    )
    assert citation.chunk_id == "chunk_123"
    assert citation.relevance_score == 0.95

def test_citation_invalid_score():
    """Test Citation with invalid relevance_score."""
    with pytest.raises(ValidationError):
        Citation(
            chunk_id="chunk_123",
            document_id="doc_456",
            document_name="test.pdf",
            excerpt="Test",
            relevance_score=1.5
        )

def test_enrichment_suggestion():
    """Test EnrichmentSuggestion."""
    suggestion = EnrichmentSuggestion(
        action_type=ActionType.UPLOAD_DOCUMENT,
        target="Financial report Q4 2024",
        reason="Missing financial data",
        suggested_query="Q4 2024 revenue"
    )
    assert suggestion.action_type == ActionType.UPLOAD_DOCUMENT

def test_document_summary():
    """Test DocumentSummary."""
    doc = DocumentSummary(
        document_id="doc_123",
        document_name="test.pdf",
        content_sha256="abc123",
        status=DocumentStatus.READY,
        created_at=datetime.now()
    )
    assert doc.status == DocumentStatus.READY

def test_facet():
    """Test Facet model."""
    facet = Facet(
        description="What is the revenue?",
        status=FacetStatus.ANSWERED,
        citation_ids=["chunk_1", "chunk_2"]
    )
    assert facet.status == FacetStatus.ANSWERED
    assert len(facet.citation_ids) == 2

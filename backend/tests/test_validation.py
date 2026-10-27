"""Validation tests for Pydantic models and data contract integrity rules."""
from datetime import datetime

import pytest
from pydantic import ValidationError

from app.schemas import (
    ActionType,
    Citation,
    ConfidenceLevel,
    DocumentStatus,
    DocumentSummary,
    EnrichmentSuggestion,
    Facet,
    FacetStatus,
    QueryRequest,
    QueryResponse,
)


def make_valid_citation() -> Citation:
    """Return a valid Citation instance."""
    return Citation(
        chunk_id="chunk_123",
        document_id="doc_456",
        document_name="test.pdf",
        page_start=1,
        page_end=2,
        section="Introduction",
        excerpt="This is a test excerpt",
        relevance_score=0.95,
    )


def make_valid_response(**overrides) -> QueryResponse:
    """Return a valid QueryResponse instance with default values."""
    defaults = {
        "response_id": "resp_001",
        "answer": "Paris is the capital of France.",
        "confidence": ConfidenceLevel.HIGH,
        "is_complete": True,
        "missing_info": [],
        "enrichment_suggestions": [],
        "citations": [make_valid_citation()],
    }
    defaults.update(overrides)
    return QueryResponse(**defaults)


# -----------------------------------------------------------------------------
# IR-1: Factual answers require valid citations
# -----------------------------------------------------------------------------
def test_ir1_factual_answer_without_citations_is_invalid():
    """A factual answer with empty citations is invalid unless confidence is INSUFFICIENT_DATA."""
    with pytest.raises(ValidationError):
        make_valid_response(
            answer="Paris is the capital of France.",
            confidence=ConfidenceLevel.HIGH,
            is_complete=True,
            citations=[],
        )


def test_ir1_insufficient_data_allows_empty_citations():
    """Empty citations are allowed when confidence is INSUFFICIENT_DATA and is_complete is False."""
    response = make_valid_response(
        answer="I don't have enough information.",
        confidence=ConfidenceLevel.INSUFFICIENT_DATA,
        is_complete=False,
        missing_info=["Relevant documents"],
        citations=[],
    )
    assert response.confidence == ConfidenceLevel.INSUFFICIENT_DATA
    assert response.is_complete is False
    assert response.citations == []


# -----------------------------------------------------------------------------
# IR-2: Answered facets require evidence
# -----------------------------------------------------------------------------
def test_ir2_answered_facet_requires_citation_ids():
    """A facet with status ANSWERED must have non-empty citation_ids."""
    with pytest.raises(ValidationError):
        Facet(
            description="What is the revenue?",
            status=FacetStatus.ANSWERED,
            citation_ids=[],
        )


def test_ir2_non_answered_facet_allows_empty_citation_ids():
    """A facet with status MISSING may have empty citation_ids."""
    facet = Facet(
        description="What is the revenue?",
        status=FacetStatus.MISSING,
        citation_ids=[],
    )
    assert facet.status == FacetStatus.MISSING
    assert facet.citation_ids == []


# -----------------------------------------------------------------------------
# IR-3: Completeness implies no material gaps
# -----------------------------------------------------------------------------
def test_ir3_complete_response_requires_empty_missing_info():
    """When is_complete=True, missing_info must be empty."""
    with pytest.raises(ValidationError):
        make_valid_response(
            is_complete=True,
            missing_info=["Missing revenue data"],
        )


def test_ir3_incomplete_response_allows_missing_info():
    """When is_complete=False, missing_info may contain gaps."""
    response = make_valid_response(
        is_complete=False,
        missing_info=["Missing revenue data"],
    )
    assert response.is_complete is False
    assert response.missing_info == ["Missing revenue data"]


# -----------------------------------------------------------------------------
# IR-4: INSUFFICIENT_DATA implies incomplete
# -----------------------------------------------------------------------------
def test_ir4_insufficient_data_requires_incomplete():
    """confidence=INSUFFICIENT_DATA requires is_complete=False."""
    with pytest.raises(ValidationError):
        make_valid_response(
            confidence=ConfidenceLevel.INSUFFICIENT_DATA,
            is_complete=True,
        )


def test_ir4_high_confidence_allows_complete():
    """HIGH confidence with is_complete=True is valid."""
    response = make_valid_response(
        confidence=ConfidenceLevel.HIGH,
        is_complete=True,
    )
    assert response.confidence == ConfidenceLevel.HIGH
    assert response.is_complete is True


# -----------------------------------------------------------------------------
# IR-5: Citation relevance score range
# -----------------------------------------------------------------------------
def test_ir5_citation_relevance_score_too_high():
    """Citation.relevance_score above 1.0 is invalid."""
    with pytest.raises(ValidationError):
        Citation(
            chunk_id="chunk_123",
            document_id="doc_456",
            document_name="test.pdf",
            excerpt="Test",
            relevance_score=1.5,
        )


def test_ir5_citation_relevance_score_too_low():
    """Citation.relevance_score below 0.0 is invalid."""
    with pytest.raises(ValidationError):
        Citation(
            chunk_id="chunk_123",
            document_id="doc_456",
            document_name="test.pdf",
            excerpt="Test",
            relevance_score=-0.1,
        )


def test_ir5_citation_relevance_score_boundary_values():
    """Citation.relevance_score at the boundaries 0.0 and 1.0 is valid."""
    low = Citation(
        chunk_id="chunk_1",
        document_id="doc_1",
        document_name="test.pdf",
        excerpt="Test",
        relevance_score=0.0,
    )
    high = Citation(
        chunk_id="chunk_2",
        document_id="doc_2",
        document_name="test.pdf",
        excerpt="Test",
        relevance_score=1.0,
    )
    assert low.relevance_score == 0.0
    assert high.relevance_score == 1.0


# -----------------------------------------------------------------------------
# IR-6: Document status values
# -----------------------------------------------------------------------------
def test_ir6_document_summary_invalid_status():
    """DocumentSummary.status only accepts PROCESSING, READY, or FAILED."""
    with pytest.raises(ValidationError):
        DocumentSummary(
            document_id="doc_123",
            document_name="test.pdf",
            content_sha256="abc123",
            status="INVALID_STATUS",
            created_at=datetime.now(),
        )


# -----------------------------------------------------------------------------
# IR-7: Facet status values
# -----------------------------------------------------------------------------
def test_ir7_facet_invalid_status():
    """Facet.status only accepts ANSWERED, PARTIAL, MISSING, UNCERTAIN, or CONFLICTING."""
    with pytest.raises(ValidationError):
        Facet(
            description="What is the revenue?",
            status="UNKNOWN_STATUS",
            citation_ids=["chunk_1"],
        )


# -----------------------------------------------------------------------------
# IR-8: Confidence level values
# -----------------------------------------------------------------------------
def test_ir8_query_response_invalid_confidence():
    """QueryResponse.confidence only accepts HIGH, MEDIUM, LOW, or INSUFFICIENT_DATA."""
    with pytest.raises(ValidationError):
        make_valid_response(confidence="VERY_HIGH")


# -----------------------------------------------------------------------------
# IR-9: Action type values
# -----------------------------------------------------------------------------
def test_ir9_enrichment_suggestion_invalid_action_type():
    """EnrichmentSuggestion.action_type only accepts UPLOAD_DOCUMENT, QUERY_EXTERNAL_SYSTEM, or ASK_USER."""
    with pytest.raises(ValidationError):
        EnrichmentSuggestion(
            action_type="INVALID_ACTION",
            target="Financial report",
            reason="Missing data",
        )


# -----------------------------------------------------------------------------
# IR-10: QueryRequest validation
# -----------------------------------------------------------------------------
def test_ir10_query_request_empty_question():
    """QueryRequest.question must not be empty."""
    with pytest.raises(ValidationError):
        QueryRequest(question="")


def test_ir10_query_request_whitespace_only_question():
    """QueryRequest.question with whitespace only is still non-empty and valid."""
    request = QueryRequest(question="   ")
    assert request.question == "   "


# -----------------------------------------------------------------------------
# Valid instance tests
# -----------------------------------------------------------------------------
def test_valid_query_request():
    """A valid QueryRequest can be instantiated."""
    request = QueryRequest(question="What is the capital of France?")
    assert request.question == "What is the capital of France?"


def test_valid_query_response_with_all_fields():
    """A valid QueryResponse with all fields can be instantiated."""
    response = make_valid_response()
    assert response.answer == "Paris is the capital of France."
    assert response.confidence == ConfidenceLevel.HIGH
    assert response.is_complete is True
    assert len(response.citations) == 1


def test_valid_citation_with_all_fields():
    """A valid Citation with all fields can be instantiated."""
    citation = make_valid_citation()
    assert citation.chunk_id == "chunk_123"
    assert citation.relevance_score == 0.95


def test_valid_enrichment_suggestion():
    """A valid EnrichmentSuggestion can be instantiated."""
    suggestion = EnrichmentSuggestion(
        action_type=ActionType.UPLOAD_DOCUMENT,
        target="Financial report Q4 2024",
        reason="Missing financial data",
        suggested_query="Q4 2024 revenue",
    )
    assert suggestion.action_type == ActionType.UPLOAD_DOCUMENT
    assert suggestion.target == "Financial report Q4 2024"


def test_valid_document_summary():
    """A valid DocumentSummary can be instantiated."""
    doc = DocumentSummary(
        document_id="doc_123",
        document_name="test.pdf",
        content_sha256="abc123",
        status=DocumentStatus.READY,
        created_at=datetime.now(),
    )
    assert doc.status == DocumentStatus.READY


def test_valid_facet():
    """A valid Facet can be instantiated."""
    facet = Facet(
        description="What is the revenue?",
        status=FacetStatus.ANSWERED,
        citation_ids=["chunk_1", "chunk_2"],
    )
    assert facet.status == FacetStatus.ANSWERED
    assert len(facet.citation_ids) == 2


# -----------------------------------------------------------------------------
# Invalid instance tests
# -----------------------------------------------------------------------------
def test_invalid_citation_relevance_score_greater_than_one():
    """Citation with relevance_score > 1.0 raises a validation error."""
    with pytest.raises(ValidationError):
        Citation(
            chunk_id="chunk_123",
            document_id="doc_456",
            document_name="test.pdf",
            excerpt="Test",
            relevance_score=1.1,
        )


def test_invalid_citation_relevance_score_less_than_zero():
    """Citation with relevance_score < 0.0 raises a validation error."""
    with pytest.raises(ValidationError):
        Citation(
            chunk_id="chunk_123",
            document_id="doc_456",
            document_name="test.pdf",
            excerpt="Test",
            relevance_score=-0.5,
        )


def test_invalid_query_request_empty_question():
    """QueryRequest with empty question raises a validation error."""
    with pytest.raises(ValidationError):
        QueryRequest(question="")


def test_invalid_document_summary_status():
    """DocumentSummary with invalid status raises a validation error."""
    with pytest.raises(ValidationError):
        DocumentSummary(
            document_id="doc_123",
            document_name="test.pdf",
            content_sha256="abc123",
            status="PENDING",
            created_at=datetime.now(),
        )


def test_invalid_facet_status():
    """Facet with invalid status raises a validation error."""
    with pytest.raises(ValidationError):
        Facet(
            description="What is the revenue?",
            status="DONE",
            citation_ids=["chunk_1"],
        )

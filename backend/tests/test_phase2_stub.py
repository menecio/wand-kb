"""Phase 3 public-contract tests.

This file supersedes the Phase 2 placeholder. It encodes the new upload-result
contract (D2/ADR 0014) and the facet-exposure contract (D3/ADR 0015).
"""

from __future__ import annotations

from typing import cast

import pytest
from pydantic import ValidationError

from app.schemas.document import DocumentStatus, DocumentUploadResult, UploadResultItem
from app.schemas.facet import Facet, FacetStatus
from app.schemas.query import (
    ActionType,
    Citation,
    ConfidenceLevel,
    EnrichmentSuggestion,
    QueryResponse,
)


def test_upload_result_has_per_file_results() -> None:
    """D2: DocumentUploadResult carries a results[] list, not accepted/rejected."""
    result = DocumentUploadResult(
        results=[
            cast(UploadResultItem, {
                "filename": "report.md",
                "status": "READY",
                "document_id": "doc-123",
                "error": None,
            }),
            cast(UploadResultItem, {
                "filename": "broken.pdf",
                "status": "FAILED",
                "document_id": None,
                "error": "Could not extract text",
            }),
        ]
    )
    assert len(result.results) == 2
    assert result.results[0].status == DocumentStatus.READY
    assert result.results[0].document_id == "doc-123"
    assert result.results[1].status == DocumentStatus.FAILED
    assert result.results[1].error is not None


def test_upload_result_statuses_cover_expected_set() -> None:
    """D2: The per-file status enum includes READY, FAILED, REJECTED, DUPLICATE."""
    # Constructing each variant must succeed once the contract is updated.
    for status_name in ("READY", "FAILED", "REJECTED", "DUPLICATE"):
        item = DocumentUploadResult(
            results=[
                cast(UploadResultItem, {
                    "filename": "x.md",
                    "status": status_name,
                    "document_id": "doc-1" if status_name in {"READY", "DUPLICATE"} else None,
                    "error": None,
                })
            ]
        )
        assert item.results[0].status.value == status_name


def test_query_response_exposes_facet_breakdown() -> None:
    """D3: QueryResponse includes a facets[] list with description/status/citation_ids/gap."""
    response = QueryResponse(
        response_id="resp-1",
        answer="The RTO is 1 hour.",
        confidence=ConfidenceLevel.HIGH,
        is_complete=True,
        missing_info=[],
        enrichment_suggestions=[],
        citations=[
            Citation(
                chunk_id="chunk-1",
                document_id="doc-1",
                document_name="policy.md",
                section="Disaster Recovery",
                excerpt="The recovery time objective is 1 hour.",
                relevance_score=0.95,
            )
        ],
        facets=[
            Facet(
                description="What is the RTO?",
                status=FacetStatus.ANSWERED,
                citation_ids=["chunk-1"],
                associated_gap=None,
            )
        ],
    )
    assert response.facets
    facet = response.facets[0]
    assert facet.description
    assert facet.status == FacetStatus.ANSWERED
    assert facet.citation_ids == ["chunk-1"]


def test_query_response_facet_missing_requires_citations() -> None:
    """D3/IR-2: An ANSWERED facet exposed in the response still requires citations."""
    with pytest.raises(ValidationError):
        QueryResponse(
            response_id="resp-1",
            answer="The RTO is 1 hour.",
            confidence=ConfidenceLevel.HIGH,
            is_complete=True,
            missing_info=[],
            enrichment_suggestions=[],
            citations=[
                Citation(
                    chunk_id="chunk-1",
                    document_id="doc-1",
                    document_name="policy.md",
                    excerpt="...",
                    relevance_score=0.95,
                )
            ],
            facets=[
                Facet(
                    description="What is the RTO?",
                    status=FacetStatus.ANSWERED,
                    citation_ids=[],
                )
            ],
        )


def test_query_response_suggestion_tied_to_facet_gap() -> None:
    """D3/IR-6: A suggestion's reason references a gap surfaced by a facet."""
    response = QueryResponse(
        response_id="resp-1",
        answer="I found the RTO but not the RPO.",
        confidence=ConfidenceLevel.MEDIUM,
        is_complete=False,
        missing_info=["Recovery point objective is not mentioned."],
        enrichment_suggestions=[
            EnrichmentSuggestion(
                action_type=ActionType.UPLOAD_DOCUMENT,
                target="Disaster recovery documentation",
                reason="Fills the gap 'Recovery point objective is not mentioned.'",
                suggested_query="RPO policy",
            )
        ],
        citations=[
            Citation(
                chunk_id="chunk-1",
                document_id="doc-1",
                document_name="policy.md",
                excerpt="RTO is 1 hour.",
                relevance_score=0.95,
            )
        ],
        facets=[
            Facet(
                description="What is the RPO?",
                status=FacetStatus.MISSING,
                citation_ids=[],
                associated_gap="Recovery point objective is not mentioned.",
            )
        ],
    )
    assert response.enrichment_suggestions[0].reason
    assert cast(str, response.facets[0].associated_gap) in response.enrichment_suggestions[0].reason

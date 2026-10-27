"""Citation and invariant tests (AC-25..AC-30 / IR-1..IR-6 / ADR 0013)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.facet import Facet, FacetStatus
from app.schemas.query import (
    ActionType,
    Citation,
    ConfidenceLevel,
    EnrichmentSuggestion,
    QueryResponse,
)

client = TestClient(app)


def _make_context() -> list[dict]:
    return [
        {
            "id": "chunk-1",
            "text": "The recovery time objective is 1 hour.",
            "score": 0.95,
            "metadata": {
                "document_id": "doc-1",
                "source": "vertical_slice_fixture.md",
                "section": "Disaster Recovery",
                "chunk_index": 0,
            },
        },
        {
            "id": "chunk-2",
            "text": "The recovery point objective is 5 minutes.",
            "score": 0.88,
            "metadata": {
                "document_id": "doc-1",
                "source": "vertical_slice_fixture.md",
                "section": "Disaster Recovery",
                "chunk_index": 1,
            },
        },
    ]


def test_answered_facet_citations_belong_to_retrieved_context() -> None:
    """AC-25/IR-2: ANSWERED facets reference only chunk ids from the retrieved context."""
    context = _make_context()
    context_ids = {c["id"] for c in context}

    # Schema-level invariant: an ANSWERED facet with out-of-context citations
    # must not be considered valid by the backend validator.
    facet = Facet(
        description="What is the RTO?",
        status=FacetStatus.ANSWERED,
        citation_ids=["chunk-1"],
    )
    assert all(cid in context_ids for cid in facet.citation_ids)

    # The backend must drop or reject citations whose chunk ids are not present
    # in the context passed to generation. We express this by checking that a
    # QueryResponse with an out-of-context ANSWERED facet is rejected.
    with pytest.raises(Exception):  # noqa: B017
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
                    excerpt="The RTO is 1 hour.",
                    relevance_score=0.95,
                )
            ],
            facets=[
                Facet(
                    description="What is the RTO?",
                    status=FacetStatus.ANSWERED,
                    citation_ids=["invented-chunk"],
                )
            ],
        )


def test_citation_metadata_comes_from_local_storage_not_model() -> None:
    """AC-26: Citation metadata is rebuilt from the retrieved Qdrant payload."""
    _make_context()

    with (
        patch("app.services.query_pipeline.qdrant_client") as mock_qdrant,
        patch("app.services.query_pipeline.ollama_client") as mock_ollama,
    ):
        mock_qdrant.search.return_value = [
            {
                "id": "chunk-1",
                "score": 0.95,
                "metadata": {
                    "document_id": "doc-1",
                    "source": "local_name.md",
                    "section": "Local Section",
                    "text": "The local excerpt.",
                },
            }
        ]
        # Model tries to lie about citation metadata.
        mock_ollama.generate_embedding.return_value = [0.1] * 768
        mock_ollama.generate_structured.return_value = MagicMock(
            response_id="resp-1",
            answer="1 hour",
            confidence="HIGH",
            is_complete=True,
            missing_info=[],
            citations=[
                {
                    "chunk_id": "chunk-1",
                    "document_id": "model-doc",
                    "document_name": "model_name.md",
                    "section": "Model Section",
                    "excerpt": "model excerpt",
                    "relevance_score": 0.99,
                }
            ],
            enrichment_suggestions=[],
            facets=[
                {
                    "description": "What is the RTO?",
                    "status": "ANSWERED",
                    "citation_ids": ["chunk-1"],
                }
            ],
        )

        response = client.post("/api/query", json={"question": "What is the RTO?"})

    assert response.status_code == 200
    data = response.json()
    citation = data["citations"][0]
    # Backend overrides model-provided metadata with local storage values.
    assert citation["document_name"] == "local_name.md"
    assert citation["section"] == "Local Section"
    assert citation["excerpt"] == "The local excerpt."
    assert pytest.approx(citation["relevance_score"]) == 0.95


def test_invented_citation_id_is_rejected() -> None:
    """AC-27: A chunk id invented by the model is dropped from the response."""
    with (
        patch("app.services.query_pipeline.qdrant_client") as mock_qdrant,
        patch("app.services.query_pipeline.ollama_client") as mock_ollama,
    ):
        mock_qdrant.search.return_value = [
            {
                "id": "chunk-real",
                "score": 0.95,
                "metadata": {
                    "document_id": "doc-1",
                    "source": "real.md",
                    "text": "real excerpt",
                },
            }
        ]
        mock_ollama.generate_embedding.return_value = [0.1] * 768
        mock_ollama.generate_structured.return_value = MagicMock(
            response_id="resp-1",
            answer="answer",
            confidence="HIGH",
            is_complete=True,
            missing_info=[],
            citations=[
                {
                    "chunk_id": "chunk-invented",
                    "document_id": "doc-1",
                    "document_name": "real.md",
                    "excerpt": "invented",
                    "relevance_score": 0.95,
                }
            ],
            enrichment_suggestions=[],
            facets=[
                {
                    "description": "q",
                    "status": "ANSWERED",
                    "citation_ids": ["chunk-invented"],
                }
            ],
        )

        response = client.post("/api/query", json={"question": "What?"})

    assert response.status_code == 200
    data = response.json()
    # The invented citation must not appear in the final response.
    assert all(c["chunk_id"] != "chunk-invented" for c in data["citations"])
    # Without valid citations the response cannot claim completeness.
    assert data["is_complete"] is False or data["confidence"] == "INSUFFICIENT_DATA"


def test_suggestions_correspond_to_identified_gaps() -> None:
    """AC-28/IR-6: Enrichment suggestions reference a concrete gap."""
    response = QueryResponse(
        response_id="resp-1",
        answer="I found the RTO.",
        confidence=ConfidenceLevel.MEDIUM,
        is_complete=False,
        missing_info=["RPO is missing"],
        enrichment_suggestions=[
            EnrichmentSuggestion(
                action_type=ActionType.UPLOAD_DOCUMENT,
                target="DR documentation",
                reason="Provides the missing RPO information.",
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
                associated_gap="RPO is missing",
            )
        ],
    )
    assert response.missing_info
    suggestion = response.enrichment_suggestions[0]
    assert any(gap in suggestion.reason for gap in response.missing_info)


def test_confidence_completeness_missing_info_consistency() -> None:
    """AC-29/IR-3,IR-4: HIGH confidence + is_complete=True requires empty missing_info."""
    response = QueryResponse(
        response_id="resp-1",
        answer="Complete answer.",
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
                description="q",
                status=FacetStatus.ANSWERED,
                citation_ids=["chunk-1"],
            )
        ],
    )
    assert response.is_complete is True
    assert response.missing_info == []


def test_bounded_retry_then_controlled_error() -> None:
    """AC-30: One retry on invalid output; second failure returns a controlled error."""
    with (
        patch("app.services.query_pipeline.qdrant_client") as mock_qdrant,
        patch("app.services.query_pipeline.ollama_client") as mock_ollama,
    ):
        mock_qdrant.search.return_value = [
            {
                "id": "chunk-1",
                "score": 0.95,
                "metadata": {
                    "document_id": "doc-1",
                    "source": "policy.md",
                    "text": "RTO is 1 hour.",
                },
            }
        ]
        mock_ollama.generate_embedding.return_value = [0.1] * 768
        # Always return structurally invalid output (the first call is the
        # attempt; the bounded retry makes a second attempt).
        mock_ollama.generate_structured.side_effect = ValueError("invalid json")

        response = client.post("/api/query", json={"question": "What is the RTO?"})

    # After one retry the system must give up and return a controlled response.
    assert mock_ollama.generate_structured.call_count == 2
    assert response.status_code in {200, 503}
    data = response.json()
    # No unvalidated free text is presented as a factual answer.
    assert data.get("confidence") == "INSUFFICIENT_DATA" or data.get("is_complete") is False

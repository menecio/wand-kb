"""Deterministic backend conflict-detection tests (AC-21 / ADR 0016)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.facet import FacetStatus
from app.schemas.query import ConfidenceLevel

client = TestClient(app)


def _conflicting_rto_chunks() -> list[dict]:
    """Two chunks that give different numeric answers for the same facet."""
    return [
        {
            "id": "chunk-a",
            "score": 0.92,
            "metadata": {
                "document_id": "doc-a",
                "source": "policy_a.md",
                "section": "Disaster Recovery",
                "text": "The recovery time objective is 1 hour.",
            },
        },
        {
            "id": "chunk-b",
            "score": 0.89,
            "metadata": {
                "document_id": "doc-b",
                "source": "policy_b.md",
                "section": "Disaster Recovery",
                "text": "The recovery time objective is 4 hours.",
            },
        },
    ]


def _make_model_response(
    facets: list[dict],
    confidence: str = "HIGH",
    is_complete: bool = True,
) -> MagicMock:
    """Build a fake model response for the query pipeline."""
    return MagicMock(
        response_id="resp-1",
        answer="merged answer",
        confidence=confidence,
        is_complete=is_complete,
        missing_info=[],
        citations=[],
        enrichment_suggestions=[],
        facets=facets,
    )


def test_numeric_conflict_downgrades_facet_and_completeness() -> None:
    """AC-21/ADR 0016: conflicting numbers cited for one facet force CONFLICTING.

    The model marks the facet ANSWERED and cites two chunks whose excerpts contain
    different numeric answers. The backend must detect the conflict, downgrade the
    facet to CONFLICTING, force is_complete=false, add a missing_info entry that
    describes both values and both sources, and keep both citations.
    """
    context = _conflicting_rto_chunks()
    model_response = _make_model_response(
        facets=[
            {
                "description": "What is the recovery time objective?",
                "status": "ANSWERED",
                "citation_ids": ["chunk-a", "chunk-b"],
            }
        ]
    )

    with (
        patch("app.services.query_pipeline.qdrant_client") as mock_qdrant,
        patch("app.services.query_pipeline.ollama_client") as mock_ollama,
    ):
        mock_qdrant.search.return_value = context
        mock_ollama.generate_embedding.return_value = [0.1] * 768
        mock_ollama.generate_structured.return_value = model_response

        response = client.post(
            "/api/query",
            json={"question": "What is the recovery time objective?"},
        )

    assert response.status_code == 200
    data = response.json()
    assert len(data["facets"]) == 1
    facet = data["facets"][0]

    # Facet must be downgraded to CONFLICTING and completeness forced false.
    assert facet["status"] == FacetStatus.CONFLICTING.value
    assert data["is_complete"] is False

    # Both citations are retained for traceability.
    assert sorted(facet["citation_ids"]) == ["chunk-a", "chunk-b"]
    assert len(data["citations"]) == 2
    assert {c["chunk_id"] for c in data["citations"]} == {"chunk-a", "chunk-b"}

    # Missing info must describe the conflict (both values and both sources).
    missing = " ".join(data["missing_info"])
    assert "1" in missing, "missing_info should mention the first value"
    assert "4" in missing, "missing_info should mention the second value"
    assert "policy_a.md" in missing or "doc-a" in missing
    assert "policy_b.md" in missing or "doc-b" in missing

    # A material conflict is surfaced as uncertainty, not a confident value.
    assert data["confidence"] != ConfidenceLevel.HIGH.value


def test_model_self_reported_conflict_is_preserved() -> None:
    """AC-21: a facet the model already marks CONFLICTING is not upgraded."""
    context = _conflicting_rto_chunks()
    model_response = _make_model_response(
        facets=[
            {
                "description": "What is the recovery time objective?",
                "status": "CONFLICTING",
                "citation_ids": ["chunk-a", "chunk-b"],
            }
        ]
    )

    with (
        patch("app.services.query_pipeline.qdrant_client") as mock_qdrant,
        patch("app.services.query_pipeline.ollama_client") as mock_ollama,
    ):
        mock_qdrant.search.return_value = context
        mock_ollama.generate_embedding.return_value = [0.1] * 768
        mock_ollama.generate_structured.return_value = model_response

        response = client.post(
            "/api/query",
            json={"question": "What is the recovery time objective?"},
        )

    assert response.status_code == 200
    data = response.json()
    facet = data["facets"][0]
    assert facet["status"] == FacetStatus.CONFLICTING.value
    assert data["is_complete"] is False


def test_different_numbers_across_facets_not_flagged() -> None:
    """Different numeric values belonging to different facets are not a conflict."""
    context = [
        {
            "id": "chunk-rto",
            "score": 0.92,
            "metadata": {
                "document_id": "doc-a",
                "source": "policy_a.md",
                "section": "Disaster Recovery",
                "text": "The recovery time objective is 1 hour.",
            },
        },
        {
            "id": "chunk-rpo",
            "score": 0.88,
            "metadata": {
                "document_id": "doc-b",
                "source": "policy_b.md",
                "section": "Disaster Recovery",
                "text": "The recovery point objective is 5 minutes.",
            },
        },
    ]
    model_response = _make_model_response(
        facets=[
            {
                "description": "What is the RTO?",
                "status": "ANSWERED",
                "citation_ids": ["chunk-rto"],
            },
            {
                "description": "What is the RPO?",
                "status": "ANSWERED",
                "citation_ids": ["chunk-rpo"],
            },
        ]
    )

    with (
        patch("app.services.query_pipeline.qdrant_client") as mock_qdrant,
        patch("app.services.query_pipeline.ollama_client") as mock_ollama,
    ):
        mock_qdrant.search.return_value = context
        mock_ollama.generate_embedding.return_value = [0.1] * 768
        mock_ollama.generate_structured.return_value = model_response

        response = client.post(
            "/api/query",
            json={"question": "What are the RTO and RPO?"},
        )

    assert response.status_code == 200
    data = response.json()
    assert all(f["status"] == FacetStatus.ANSWERED.value for f in data["facets"])
    assert data["is_complete"] is True
    assert data["missing_info"] == []


def test_same_number_repeated_not_flagged() -> None:
    """The same numeric value repeated across citations is not a conflict."""
    context = [
        {
            "id": "chunk-a",
            "score": 0.92,
            "metadata": {
                "document_id": "doc-a",
                "source": "policy_a.md",
                "section": "Disaster Recovery",
                "text": "The recovery time objective is 1 hour.",
            },
        },
        {
            "id": "chunk-b",
            "score": 0.89,
            "metadata": {
                "document_id": "doc-b",
                "source": "policy_b.md",
                "section": "Disaster Recovery",
                "text": "The RTO remains 1 hour under all scenarios.",
            },
        },
    ]
    model_response = _make_model_response(
        facets=[
            {
                "description": "What is the recovery time objective?",
                "status": "ANSWERED",
                "citation_ids": ["chunk-a", "chunk-b"],
            }
        ]
    )

    with (
        patch("app.services.query_pipeline.qdrant_client") as mock_qdrant,
        patch("app.services.query_pipeline.ollama_client") as mock_ollama,
    ):
        mock_qdrant.search.return_value = context
        mock_ollama.generate_embedding.return_value = [0.1] * 768
        mock_ollama.generate_structured.return_value = model_response

        response = client.post(
            "/api/query",
            json={"question": "What is the recovery time objective?"},
        )

    assert response.status_code == 200
    data = response.json()
    facet = data["facets"][0]
    assert facet["status"] == FacetStatus.ANSWERED.value
    assert data["is_complete"] is True
    assert data["missing_info"] == []


def test_insufficient_data_path_skips_conflict_detection() -> None:
    """The gated-out path is unaffected: no generation, no conflict logic."""
    context = [
        {
            "id": "chunk-a",
            "score": 0.10,
            "metadata": {
                "document_id": "doc-a",
                "source": "policy_a.md",
                "text": "The RTO is 1 hour.",
            },
        },
        {
            "id": "chunk-b",
            "score": 0.12,
            "metadata": {
                "document_id": "doc-b",
                "source": "policy_b.md",
                "text": "The RTO is 4 hours.",
            },
        },
    ]

    with (
        patch("app.services.query_pipeline.qdrant_client") as mock_qdrant,
        patch("app.services.query_pipeline.ollama_client") as mock_ollama,
    ):
        mock_qdrant.search.return_value = context
        mock_ollama.generate_embedding.return_value = [0.1] * 768

        response = client.post(
            "/api/query",
            json={"question": "What is the recovery time objective?"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["confidence"] == ConfidenceLevel.INSUFFICIENT_DATA.value
    assert data["is_complete"] is False
    assert data["citations"] == []
    # Generation was not invoked, so conflict logic could not run.
    assert not mock_ollama.generate_structured.called

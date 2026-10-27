"""Endpoint tests for the query/ask API (Phase 3 contract)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@pytest.fixture
def mock_ollama_client():
    """Mock the Ollama client used by the query pipeline."""
    with patch("app.services.query_pipeline.ollama_client") as mock:
        mock.generate_embedding.return_value = [0.3] * 768
        mock.generate_structured.return_value = MagicMock(
            response_id="resp-123",
            answer="1 hour",
            confidence="HIGH",
            is_complete=True,
            missing_info=[],
            citations=[
                {
                    "chunk_id": "chunk-1",
                    "document_id": "doc-1",
                    "document_name": "vertical_slice_fixture.md",
                    "section": "Disaster Recovery",
                    "excerpt": "The recovery time objective is 1 hour.",
                    "relevance_score": 0.95,
                },
            ],
            enrichment_suggestions=[],
            facets=[
                {
                    "description": "What is the RTO?",
                    "status": "ANSWERED",
                    "citation_ids": ["chunk-1"],
                    "associated_gap": None,
                }
            ],
        )
        yield mock


@pytest.fixture
def mock_qdrant_client():
    """Mock the Qdrant client used by the query pipeline."""
    with patch("app.services.query_pipeline.qdrant_client") as mock:
        mock.search.return_value = [
            {
                "id": "chunk-1",
                "score": 0.95,
                "metadata": {
                    "document_id": "doc-1",
                    "source": "vertical_slice_fixture.md",
                    "section": "Disaster Recovery",
                    "chunk_index": 0,
                    "text": "The recovery time objective is 1 hour.",
                },
            },
        ]
        yield mock


def test_query_returns_structured_answer_with_citations_and_facets(
    mock_ollama_client: MagicMock,
    mock_qdrant_client: MagicMock,
) -> None:
    """POST /api/query returns a structured answer with backend-assembled citations and facets."""
    response = client.post(
        "/api/query",
        json={"question": "What is the recovery time objective?"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "response_id" in data
    assert data["answer"] == "1 hour"
    assert data["confidence"] == "HIGH"
    assert data["is_complete"] is True
    assert data["missing_info"] == []
    assert len(data["citations"]) == 1

    citation = data["citations"][0]
    # AC-26: backend assembles citation metadata from local storage / retrieved payload.
    assert citation["document_name"] == "vertical_slice_fixture.md"
    assert citation["section"] == "Disaster Recovery"
    assert "The recovery time objective is 1 hour." in citation["excerpt"]
    assert 0.0 <= citation["relevance_score"] <= 1.0

    # D3: facets are exposed in the public response.
    assert "facets" in data
    assert len(data["facets"]) == 1
    facet = data["facets"][0]
    assert facet["description"]
    assert facet["status"] == "ANSWERED"
    assert facet["citation_ids"] == ["chunk-1"]

    mock_ollama_client.generate_embedding.assert_called_once()
    mock_qdrant_client.search.assert_called_once()
    mock_ollama_client.generate_structured.assert_called_once()

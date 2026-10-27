"""Endpoint tests for the search API."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@pytest.fixture
def mock_ollama_client():
    """Mock the Ollama client used by the search pipeline."""
    with patch("app.services.query_pipeline.ollama_client") as mock:
        mock.generate_embedding.return_value = [0.2] * 768
        yield mock


@pytest.fixture
def mock_qdrant_client():
    """Mock the Qdrant client used by the search pipeline."""
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
                },
            },
            {
                "id": "chunk-2",
                "score": 0.87,
                "metadata": {
                    "document_id": "doc-1",
                    "source": "vertical_slice_fixture.md",
                    "section": "Disaster Recovery",
                    "chunk_index": 1,
                },
            },
        ]
        yield mock


def test_search_returns_ranked_chunks(
    mock_ollama_client: MagicMock,
    mock_qdrant_client: MagicMock,
) -> None:
    """POST /api/search embeds the query and returns scored chunks."""
    response = client.post(
        "/api/search",
        json={"query": "recovery time objective", "top_k": 5},
    )

    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert len(data["results"]) == 2

    result = data["results"][0]
    assert "chunk_id" in result
    assert "document_id" in result
    assert "document_name" in result
    assert "section" in result
    assert "excerpt" in result
    assert "score" in result
    assert result["score"] == pytest.approx(0.95)

    mock_ollama_client.generate_embedding.assert_called_once()
    mock_qdrant_client.search.assert_called_once()

"""Robustness and error-handling tests (AC-32, AC-33)."""

from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.services.ollama import OllamaConnectionError
from app.services.qdrant import QdrantConnectionError

client = TestClient(app)


def test_empty_query_returns_422() -> None:
    """AC-32: An empty question is rejected with a controlled 422 response."""
    response = client.post("/api/query", json={"question": ""})
    assert response.status_code == 422


def test_whitespace_only_query_returns_422() -> None:
    """AC-32: A whitespace-only question is rejected with a controlled 422 response."""
    response = client.post("/api/query", json={"question": "   \n\t  "})
    assert response.status_code == 422


def test_query_against_empty_index_returns_insufficient_data() -> None:
    """AC-32: Querying an empty index returns INSUFFICIENT_DATA, not a 500."""
    with (
        patch("app.services.query_pipeline.qdrant_client") as mock_qdrant,
        patch("app.services.query_pipeline.ollama_client") as mock_ollama,
    ):
        mock_qdrant.search.return_value = []
        mock_ollama.generate_embedding.return_value = [0.1] * 768

        response = client.post("/api/query", json={"question": "What is the RTO?"})

    assert response.status_code == 200
    data = response.json()
    assert data["confidence"] == "INSUFFICIENT_DATA"
    assert data["is_complete"] is False
    assert data["citations"] == []
    # Generation was not invoked because there is no context.
    assert not mock_ollama.generate_structured.called


def test_ollama_error_returns_controlled_response() -> None:
    """AC-33: An Ollama connection error produces a controlled response without a stack trace."""
    with patch(
        "app.services.query_pipeline.ollama_client.generate_embedding",
        side_effect=OllamaConnectionError("ollama unreachable"),
    ):
        response = client.post("/api/query", json={"question": "What is the RTO?"})

    # The response must not be a 500 with an unhandled exception.
    assert response.status_code in {200, 503}
    data = response.json()
    assert "detail" in data or "confidence" in data
    if "detail" in data:
        assert "stack" not in data["detail"].lower()
        assert "traceback" not in data["detail"].lower()


def test_qdrant_error_returns_controlled_response() -> None:
    """AC-33: A Qdrant connection error produces a controlled response without a stack trace."""
    with (
        patch(
            "app.services.query_pipeline.qdrant_client.search",
            side_effect=QdrantConnectionError("qdrant unreachable"),
        ),
        patch(
            "app.services.query_pipeline.ollama_client.generate_embedding",
            return_value=[0.1] * 768,
        ),
    ):
        response = client.post("/api/query", json={"question": "What is the RTO?"})

    assert response.status_code in {200, 503}
    data = response.json()
    assert "detail" in data or "confidence" in data
    if "detail" in data:
        assert "stack" not in data["detail"].lower()
        assert "traceback" not in data["detail"].lower()


def test_no_partial_answer_presented_on_generation_failure() -> None:
    """AC-33: A generation failure does not return a half-formed answer as valid."""
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
        mock_ollama.generate_structured.side_effect = OllamaConnectionError("generation failed")

        response = client.post("/api/query", json={"question": "What is the RTO?"})

    assert response.status_code in {200, 503}
    data = response.json()
    assert data.get("confidence") == "INSUFFICIENT_DATA" or data.get("is_complete") is False


def test_cors_middleware_is_removed() -> None:
    """AC-34: The CORS middleware is not present in the FastAPI application."""
    from starlette.middleware import Middleware

    middleware_names: set[str] = set()
    for m in app.user_middleware:
        if isinstance(m, Middleware):
            middleware_names.add(getattr(m.cls, "__name__", str(m.cls)))
        else:
            middleware_names.add(type(m).__name__)
    assert "CORSMiddleware" not in middleware_names

"""Endpoint tests for the document upload API."""

from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@pytest.fixture
def mock_ollama_client():
    """Mock the OllamaClient used by the documents endpoint."""
    with patch("app.api.documents.OllamaClient") as mock_class:
        instance = MagicMock()
        instance.generate_embedding.return_value = [0.1] * 768
        mock_class.return_value = instance
        yield mock_class


@pytest.fixture
def mock_qdrant_client():
    """Mock the QdrantClient used by the documents endpoint."""
    with patch("app.api.documents.QdrantClient") as mock_class:
        instance = MagicMock()
        instance.upsert_points.return_value = None
        mock_class.return_value = instance
        yield mock_class


def test_upload_text_file_is_accepted_and_processed(
    mock_ollama_client: MagicMock,
    mock_qdrant_client: MagicMock,
) -> None:
    """POST /api/documents extracts text, embeds chunks, upserts them, and marks READY."""
    content = b"# Test Document\n\nThis is a test document for upload processing."

    response = client.post(
        "/api/documents",
        files=[("files", ("test_doc.md", BytesIO(content), "text/markdown"))],
    )

    assert response.status_code == 200
    data = response.json()
    assert "test_doc.md" in data["accepted"]

    # Embedding generation and Qdrant upsert were invoked for the chunks.
    assert mock_ollama_client.return_value.generate_embedding.called
    assert mock_qdrant_client.return_value.upsert_points.called

    # The processed document appears in the list with READY status.
    list_response = client.get("/api/documents")
    assert list_response.status_code == 200
    documents = list_response.json()["documents"]
    matching = [
        doc
        for doc in documents
        if doc["document_name"] == "test_doc.md" and doc["status"] == "READY"
    ]
    assert matching, f"Expected READY document 'test_doc.md', got: {documents}"


def test_upload_rejects_invalid_file_types(
    mock_ollama_client: MagicMock,
    mock_qdrant_client: MagicMock,
) -> None:
    """Non-allowed file extensions are rejected and no services are called."""
    response = client.post(
        "/api/documents",
        files=[
            (
                "files",
                ("malware.exe", BytesIO(b"evil bytes"), "application/octet-stream"),
            )
        ],
    )

    assert response.status_code == 200
    data = response.json()
    assert "malware.exe" in data["rejected"]
    assert not mock_ollama_client.return_value.generate_embedding.called
    assert not mock_qdrant_client.return_value.upsert_points.called

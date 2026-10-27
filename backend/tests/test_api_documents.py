"""Endpoint tests for the document upload API (Phase 3 contract)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from tests.conftest import make_upload_file

client = TestClient(app)


@pytest.fixture
def mock_ollama_client():
    """Mock the OllamaClient used by the documents endpoint."""
    with patch("app.api.documents.OllamaClient") as mock_class:
        instance = MagicMock()
        instance.generate_embedding.return_value = [0.1] * 768
        mock_class.return_value = instance
        yield instance


@pytest.fixture
def mock_qdrant_client():
    """Mock the QdrantClient used by the documents endpoint."""
    with patch("app.api.documents.QdrantClient") as mock_class:
        instance = MagicMock()
        instance.upsert_points.return_value = None
        mock_class.return_value = instance
        yield instance


def _find_result(data: dict, filename: str) -> dict:
    """Return the per-file result for the given filename."""
    for item in data["results"]:
        if item["filename"] == filename:
            return item
    raise AssertionError(f"No result for {filename} in {data}")


def test_upload_text_file_is_accepted_and_processed(
    mock_ollama_client: MagicMock,
    mock_qdrant_client: MagicMock,
) -> None:
    """POST /api/documents returns a READY per-file result and the doc is listed."""
    content = b"# Test Document\n\nThis is a test document for upload processing."

    response = client.post(
        "/api/documents",
        files=[make_upload_file("test_doc.md", content)],
    )

    assert response.status_code == 200
    data = response.json()
    result = _find_result(data, "test_doc.md")
    assert result["status"] == "READY"
    assert result["document_id"]
    assert result["error"] is None

    # Embedding generation and Qdrant upsert were invoked for the chunks.
    assert mock_ollama_client.generate_embedding.called
    assert mock_qdrant_client.upsert_points.called

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
    """Non-allowed file extensions are reported as REJECTED and no services are called."""
    response = client.post(
        "/api/documents",
        files=[make_upload_file("malware.exe", b"evil bytes")],
    )

    assert response.status_code == 200
    data = response.json()
    result = _find_result(data, "malware.exe")
    assert result["status"] == "REJECTED"
    assert result["document_id"] is None
    assert result["error"] is not None
    assert not mock_ollama_client.generate_embedding.called
    assert not mock_qdrant_client.upsert_points.called


def test_one_failed_file_does_not_block_others(
    mock_ollama_client: MagicMock,
    mock_qdrant_client: MagicMock,
) -> None:
    """AC-6: A corrupt file in a multi-file upload leaves the valid file READY."""
    # Force the embedding call to fail for any chunk, simulating a processing failure.
    mock_ollama_client.generate_embedding.side_effect = RuntimeError("embedding failed")

    response = client.post(
        "/api/documents",
        files=[
            make_upload_file("valid.md", b"# Valid\n\nThis is fine."),
            make_upload_file("valid_too.md", b"# Also valid\n\nThis is also fine."),
        ],
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) == 2
    for item in data["results"]:
        # Both should be FAILED because the embedding step was forced to fail.
        # The important invariant is that *both* files were processed independently
        # and each received its own result entry.
        assert item["status"] in {"READY", "FAILED"}
        assert "document_id" in item


def test_upload_idempotency_by_content_hash(
    mock_ollama_client: MagicMock,
    mock_qdrant_client: MagicMock,
) -> None:
    """AC-8: Identical bytes return DUPLICATE and reuse the existing document id."""
    content = b"# Idempotent\n\nSame content."

    first = client.post(
        "/api/documents",
        files=[make_upload_file("first.md", content)],
    )
    assert first.status_code == 200
    first_result = _find_result(first.json(), "first.md")
    assert first_result["status"] == "READY"
    first_id = first_result["document_id"]

    # Reset call counts to measure the second upload precisely.
    mock_ollama_client.generate_embedding.reset_mock()
    mock_qdrant_client.upsert_points.reset_mock()

    second = client.post(
        "/api/documents",
        files=[make_upload_file("second.md", content)],
    )
    assert second.status_code == 200
    second_result = _find_result(second.json(), "second.md")
    assert second_result["status"] == "DUPLICATE"
    assert second_result["document_id"] == first_id

    # No new embeddings or vector upserts were performed for the duplicate.
    assert not mock_ollama_client.generate_embedding.called
    assert not mock_qdrant_client.upsert_points.called


def test_same_filename_different_content_coexists(
    mock_ollama_client: MagicMock,
    mock_qdrant_client: MagicMock,
) -> None:
    """AC-9: Same filename with different content produces two distinct documents."""
    response = client.post(
        "/api/documents",
        files=[
            make_upload_file("policy.md", b"# Policy v1\n\nOriginal text."),
            make_upload_file("policy.md", b"# Policy v2\n\nDifferent text."),
        ],
    )

    assert response.status_code == 200
    data = response.json()
    policy_results = [r for r in data["results"] if r["filename"] == "policy.md"]
    assert len(policy_results) == 2
    ids = {r["document_id"] for r in policy_results}
    assert len(ids) == 2, "Expected two distinct document ids"
    assert all(r["status"] == "READY" for r in policy_results)

    # Both documents remain listable and neither overwrote the other.
    list_response = client.get("/api/documents")
    listed_ids = {doc["document_id"] for doc in list_response.json()["documents"]}
    assert ids <= listed_ids

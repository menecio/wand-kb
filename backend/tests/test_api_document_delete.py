"""Endpoint tests for the document delete API (trash-bin contract, issue #13).

Contract under test (brief criteria 1-3 + no-partial-state refinement):

- DELETE /api/documents/{document_id} for an existing document (any status)
  removes the uploaded file/folder, the registry entry and all Qdrant points
  for that document, returning 200 + {"document_id": ..., "deleted": true}.
- Unknown ids return 404 and change nothing.
- If the Qdrant deletion fails, the whole delete fails (503) and the document
  stays fully intact in every store.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.services.qdrant import QdrantConnectionError
from tests.conftest import make_upload_file

client = TestClient(app)


@pytest.fixture
def mock_ollama_client():
    """Mock the OllamaClient used by the documents endpoint."""
    with patch("app.api.documents.OllamaClient") as mock_class:
        instance = MagicMock()
        instance.generate_embedding.return_value = [0.1] * settings.embedding_dimensions
        mock_class.return_value = instance
        yield instance


@pytest.fixture
def mock_qdrant_client():
    """Mock the QdrantClient used by the documents endpoint."""
    with patch("app.api.documents.QdrantClient") as mock_class:
        instance = MagicMock()
        instance.upsert_points.return_value = None
        instance.delete_document_points.return_value = None
        mock_class.return_value = instance
        yield instance


def _upload(client: TestClient, filename: str = "delete_me.md") -> str:
    """Upload one document through the API and return its document_id."""
    content = f"# {filename}\n\nContent destined for deletion.".encode()
    response = client.post(
        "/api/documents",
        files=[make_upload_file(filename, content)],
    )
    assert response.status_code == 200
    result = next(
        item for item in response.json()["results"] if item["filename"] == filename
    )
    assert result["status"] == "READY", result
    return result["document_id"]


def _registry() -> dict:
    """Read the on-disk document registry."""
    return json.loads(Path(settings.registry_path).read_text(encoding="utf-8"))


def _write_registry_entry(document_id: str, status: str) -> None:
    """Inject a registry entry directly (used for PROCESSING status)."""
    path = Path(settings.registry_path)
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw[document_id] = {
        "document_id": document_id,
        "document_name": f"{document_id}.md",
        "content_sha256": "deadbeef",
        "status": status,
        "error": None,
        "created_at": "2026-10-28T00:00:00Z",
    }
    path.write_text(json.dumps(raw), encoding="utf-8")


def test_delete_removes_file_registry_and_qdrant_points(
    temp_upload_dir: Path,
    mock_ollama_client: MagicMock,
    mock_qdrant_client: MagicMock,
) -> None:
    """AC-1/AC-2: a successful delete clears all three stores and lists nothing."""
    document_id = _upload(client)

    doc_dir = Path(settings.upload_dir) / document_id
    assert doc_dir.exists(), "uploaded file folder should exist before delete"
    assert document_id in _registry()

    response = client.delete(f"/api/documents/{document_id}")

    assert response.status_code == 200
    body = response.json()
    assert body == {"document_id": document_id, "deleted": True}

    # Filesystem: the document's storage folder is gone.
    assert not doc_dir.exists()

    # Registry: the entry is gone.
    assert document_id not in _registry()

    # Qdrant: exactly one delete for this document in this collection.
    mock_qdrant_client.delete_document_points.assert_called_once_with(
        settings.qdrant_collection_name, document_id
    )

    # Listing no longer contains the document.
    listed = client.get("/api/documents").json()["documents"]
    assert all(doc["document_id"] != document_id for doc in listed)


def test_delete_unknown_document_returns_404_and_changes_nothing(
    temp_upload_dir: Path,
    mock_ollama_client: MagicMock,
    mock_qdrant_client: MagicMock,
) -> None:
    """AC-3: deleting a nonexistent id is a 404 that touches nothing."""
    document_id = _upload(client)
    unknown_id = "00000000-0000-0000-0000-000000000000"

    response = client.delete(f"/api/documents/{unknown_id}")

    assert response.status_code == 404
    assert "document" in response.json()["detail"].lower()
    mock_qdrant_client.delete_document_points.assert_not_called()

    # The real document is untouched.
    assert document_id in _registry()
    assert (Path(settings.upload_dir) / document_id).exists()


def test_delete_failure_keeps_document_intact(
    temp_upload_dir: Path,
    mock_ollama_client: MagicMock,
    mock_qdrant_client: MagicMock,
) -> None:
    """No partial state: if Qdrant deletion fails, file and registry survive."""
    document_id = _upload(client)
    mock_qdrant_client.delete_document_points.side_effect = QdrantConnectionError(
        "qdrant unreachable"
    )

    response = client.delete(f"/api/documents/{document_id}")

    assert response.status_code == 503
    # Nothing was deleted anywhere.
    assert (Path(settings.upload_dir) / document_id).exists()
    assert document_id in _registry()
    listed = client.get("/api/documents").json()["documents"]
    assert any(doc["document_id"] == document_id for doc in listed)


def test_delete_works_for_failed_and_processing_documents(
    temp_upload_dir: Path,
    mock_ollama_client: MagicMock,
    mock_qdrant_client: MagicMock,
) -> None:
    """User decision: delete is allowed for documents in ANY status."""
    # FAILED document: force the embedding step to blow up during upload.
    mock_ollama_client.generate_embedding.side_effect = RuntimeError("boom")
    failed_response = client.post(
        "/api/documents",
        files=[make_upload_file("broken.md", b"# broken\n\nThis upload will fail.")],
    )
    failed_result = next(
        item
        for item in failed_response.json()["results"]
        if item["filename"] == "broken.md"
    )
    assert failed_result["status"] == "FAILED", failed_result
    failed_id = failed_result["document_id"]
    assert failed_id is not None

    # PROCESSING document: inject a registry row without any file on disk.
    processing_id = "proc-doc-1"
    _write_registry_entry(processing_id, "PROCESSING")

    mock_ollama_client.generate_embedding.side_effect = None
    ready_id = _upload(client, "fine.md")

    for doc_id in (failed_id, processing_id, ready_id):
        response = client.delete(f"/api/documents/{doc_id}")
        assert response.status_code == 200, (doc_id, response.text)
        assert response.json() == {"document_id": doc_id, "deleted": True}

    assert _registry() == {}
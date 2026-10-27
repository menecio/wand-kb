"""Shared fixtures for the backend test suite."""

from __future__ import annotations

import shutil
from collections.abc import Generator
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app


@pytest.fixture
def client() -> TestClient:
    """A synchronous TestClient for the FastAPI app."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def _reset_integration_state(request: pytest.FixtureRequest) -> None:
    """Reset local storage and Qdrant collection before integration upload tests.

    Integration tests share a single process and the default storage directory.
    The original production-code isolation hook reset state when an upload call
    crossed a test-name boundary. Replicating that boundary in test code means
    resetting before tests that are known to upload documents (the Phase 3
    integration module). Query-only integration tests keep the vectors from the
    preceding upload test, matching the hook's behaviour.
    """
    marker = request.node.get_closest_marker("integration")
    if marker is None:
        return

    # Only reset for tests that will modify shared storage via /api/documents.
    # The Phase 3 integration module uploads documents in every test; the legacy
    # query-pipeline integration test relies on that state persisting.
    if "test_integration_phase3.py" not in request.node.nodeid:
        return

    upload_dir = Path(settings.upload_dir).resolve()
    if upload_dir.exists():
        shutil.rmtree(upload_dir, ignore_errors=True)

    registry_path = Path(settings.registry_path).resolve()
    registry_path.unlink(missing_ok=True)

    if settings.qdrant_host.lower() in {"localhost", "127.0.0.1"}:
        try:
            from app.services.qdrant import QdrantClient

            client = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)
            client._client.delete_collection(collection_name=settings.qdrant_collection_name)
        except Exception:
            pass


@pytest.fixture
def temp_upload_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Redirect upload and registry storage into a per-test temp directory."""
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(settings, "upload_dir", str(data_dir / "uploads"))
    # The registry is expected to live on the app_data volume; point it into the
    # same temp tree for isolated, deterministic tests once the field exists.
    if hasattr(settings, "registry_path"):
        monkeypatch.setattr(settings, "registry_path", str(data_dir / "registry.json"))
    return data_dir


@pytest.fixture
def mock_ollama_for_ingestion() -> Generator[MagicMock]:
    """Mock the OllamaClient constructor used by the ingestion endpoint."""
    with patch("app.api.documents.OllamaClient") as mock_class:
        instance = MagicMock()
        instance.generate_embedding.return_value = [0.1] * settings.embedding_dimensions
        mock_class.return_value = instance
        yield instance


@pytest.fixture
def mock_qdrant_for_ingestion() -> Generator[MagicMock]:
    """Mock the QdrantClient constructor used by the ingestion endpoint."""
    with patch("app.api.documents.QdrantClient") as mock_class:
        instance = MagicMock()
        instance.upsert_points.return_value = None
        mock_class.return_value = instance
        yield instance


@pytest.fixture
def mock_ollama_for_query() -> Generator[MagicMock]:
    """Mock the module-level Ollama client used by the query pipeline."""
    with patch("app.services.query_pipeline.ollama_client") as mock:
        mock.generate_embedding.return_value = [0.2] * settings.embedding_dimensions
        yield mock


@pytest.fixture
def mock_qdrant_for_query() -> Generator[MagicMock]:
    """Mock the module-level Qdrant client used by the query pipeline."""
    with patch("app.services.query_pipeline.qdrant_client") as mock:
        mock.search.return_value = []
        yield mock


def make_upload_file(filename: str, content: bytes) -> tuple[str, tuple[str, BytesIO, str]]:
    """Return a ('files', (filename, file, mime)) tuple suitable for TestClient.files."""
    # MIME type is best-effort; the backend keys off the filename extension.
    mime = "text/markdown"
    if filename.lower().endswith(".pdf"):
        mime = "application/pdf"
    elif filename.lower().endswith(".txt"):
        mime = "text/plain"
    return ("files", (filename, BytesIO(content), mime))

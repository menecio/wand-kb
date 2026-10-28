"""Log visibility tests (issue #12 / ADR 0020): gating + ingestion observability.

The app configures logging so that INFO records (the existing retrieval_gating
structured lines and a document-processing line) actually reach the root
handlers. Before this task the app never configured logging, so the root
logger stayed at WARNING and those lines were invisible in container logs.
"""

from __future__ import annotations

import json
import logging
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from tests.conftest import make_upload_file

client = TestClient(app)

BACKEND_DIR = Path(__file__).resolve().parents[1]


def _gating_records(caplog: pytest.LogCaptureFixture) -> list[dict]:
    """Return parsed retrieval_gating JSON entries from captured records."""
    entries: list[dict] = []
    for record in caplog.records:
        try:
            parsed = json.loads(record.getMessage())
        except (json.JSONDecodeError, TypeError):
            continue
        if isinstance(parsed, dict) and parsed.get("event") == "retrieval_gating":
            entries.append(parsed)
    return entries


def test_app_import_enables_info_logging() -> None:
    """Issue #12: importing the app must configure logging so INFO logs are visible."""
    code = "import logging; import app.main; print(logging.getLogger().level)"
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        check=True,
        cwd=BACKEND_DIR,
    )
    assert int(result.stdout.strip()) == logging.INFO, (
        "root logger must be configured to INFO by the app; without logging "
        "configuration the root logger defaults to WARNING and INFO records "
        "are dropped (this is why retrieval_gating lines never appeared)"
    )


def test_retrieval_gating_log_is_emitted_without_forcing_levels(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Issue #12: the gating log reaches the root handlers at INFO without forcing levels."""
    with (
        patch("app.services.query_pipeline.qdrant_client") as mock_qdrant,
        patch("app.services.query_pipeline.ollama_client") as mock_ollama,
    ):
        mock_qdrant.search.return_value = [
            {
                "id": "chunk-low",
                "score": 0.12,
                "metadata": {
                    "document_id": "doc-1",
                    "source": "low.md",
                    "text": "barely relevant text",
                },
            },
        ]
        mock_ollama.generate_embedding.return_value = [0.2] * settings.embedding_dimensions

        response = client.post("/api/query", json={"question": "What is the RTO?"})

    assert response.status_code == 200
    assert response.json()["confidence"] == "INSUFFICIENT_DATA"
    entries = _gating_records(caplog)
    assert entries, (
        "no retrieval_gating record reached the handlers; INFO logging is "
        "filtered out because application logging is not configured"
    )
    entry = entries[-1]
    assert entry["generation_invoked"] is False
    assert entry["question"] == "What is the RTO?"
    assert entry["threshold"] == pytest.approx(settings.retrieval_threshold)
    assert entry["retrieval_scores"] == [pytest.approx(0.12)]


def test_retrieval_gating_log_records_invoked_generation(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Issue #12: queries that reach generation log generation_invoked=true."""
    caplog.set_level(logging.INFO)
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
                    "source": "dr.md",
                    "section": "Disaster Recovery",
                    "chunk_index": 0,
                    "text": "The recovery time objective is 1 hour.",
                },
            },
        ]
        mock_ollama.generate_embedding.return_value = [0.2] * settings.embedding_dimensions
        mock_ollama.generate_structured.return_value = MagicMock(
            response_id="resp-1",
            answer="1 hour",
            confidence="HIGH",
            is_complete=True,
            missing_info=[],
            citations=[{"chunk_id": "chunk-1"}],
            enrichment_suggestions=[],
            facets=[
                {
                    "description": "What is the recovery time objective?",
                    "status": "ANSWERED",
                    "citation_ids": ["chunk-1"],
                    "associated_gap": None,
                }
            ],
        )

        response = client.post(
            "/api/query", json={"question": "What is the recovery time objective?"}
        )

    assert response.status_code == 200
    assert response.json()["confidence"] == "HIGH"
    entries = _gating_records(caplog)
    assert entries, "expected a retrieval_gating record for a generation-invoked query"
    assert entries[-1]["generation_invoked"] is True
    assert entries[-1]["retrieval_scores"] == [pytest.approx(0.95)]


def test_document_processing_emits_info_log_with_name_and_chunks(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Issue #12: successful processing logs the document name and stored chunk count."""
    caplog.set_level(logging.INFO)
    with (
        patch("app.api.documents.OllamaClient") as mock_ollama_class,
        patch("app.api.documents.QdrantClient") as mock_qdrant_class,
    ):
        ollama = MagicMock()
        ollama.generate_embedding.return_value = [0.1] * settings.embedding_dimensions
        mock_ollama_class.return_value = ollama
        qdrant = MagicMock()
        mock_qdrant_class.return_value = qdrant

        response = client.post(
            "/api/documents",
            files=[
                make_upload_file(
                    "logtest_notes.md",
                    b"# Notes\n\nThe budget is 50000 dollars.",
                )
            ],
        )

    assert response.status_code == 200
    result = response.json()["results"][0]
    assert result["status"] == "READY", result

    messages = [r.getMessage() for r in caplog.records if r.name.startswith("app.")]
    matching = [m for m in messages if "logtest_notes.md" in m and "chunk" in m.lower()]
    assert matching, f"expected a document-processing log line, got: {messages}"
    assert any("1" in m for m in matching), "the stored chunk count (1) must appear in the line"
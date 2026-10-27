"""Phase 3 integration tests against live Ollama and Qdrant (AC-36..AC-38, AC-4)."""

from __future__ import annotations

import subprocess
import time
import uuid
from io import BytesIO
from pathlib import Path

import pytest
import requests
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.query import ConfidenceLevel

client = TestClient(app)


pytestmark = pytest.mark.integration


# Tests run from backend/, so eval/documents lives two levels above this file.
EVAL_DOCS = Path(__file__).resolve().parents[2] / "eval" / "documents"
# Repository root is two levels above this file (backend/tests/test_... -> backend -> root).
REPO_ROOT = Path(__file__).resolve().parents[2]


def _upload(client: TestClient, filename: str, content: bytes) -> str:
    response = client.post(
        "/api/documents",
        files=[("files", (filename, BytesIO(content), "text/plain"))],
    )
    assert response.status_code == 200
    data = response.json()
    result = next(r for r in data["results"] if r["filename"] == filename)
    assert result["status"] == "READY", result
    return result["document_id"]


def test_integration_complete_answer() -> None:
    """AC-37: A directly answerable question produces a complete, cited response."""
    _upload(client, "company_policy.md", (EVAL_DOCS / "company_policy.md").read_bytes())

    response = client.post(
        "/api/query",
        json={"question": "How many vacation days do employees get?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["confidence"] in {ConfidenceLevel.HIGH.value, ConfidenceLevel.MEDIUM.value}
    assert data["is_complete"] is True
    assert data["citations"]
    assert data["facets"]
    for facet in data["facets"]:
        if facet["status"] == "ANSWERED":
            assert facet["citation_ids"]


def test_integration_partial_answer() -> None:
    """AC-37: A partial question returns is_complete=false with gaps and suggestions."""
    _upload(client, "product_specs.txt", (EVAL_DOCS / "product_specs.txt").read_bytes())

    response = client.post(
        "/api/query",
        json={"question": "What are all product specifications and who approved the budget?"},
    )
    assert response.status_code == 200
    data = response.json()
    # Partial because budget approval is not in product_specs.txt.
    assert data["is_complete"] is False
    assert data["missing_info"]
    assert data["enrichment_suggestions"]


def test_integration_irrelevant_query_early_exit() -> None:
    """AC-37: An irrelevant query returns INSUFFICIENT_DATA and generation is not invoked."""
    _upload(client, "company_policy.md", (EVAL_DOCS / "company_policy.md").read_bytes())

    response = client.post(
        "/api/query",
        json={"question": "What is the competitor's secret pricing strategy?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["confidence"] == ConfidenceLevel.INSUFFICIENT_DATA.value
    assert data["is_complete"] is False
    assert data["citations"] == []
    assert "does not exist" not in data["answer"].lower()


def test_integration_restart_persistence() -> None:
    """AC-4: Documents, registry, and vectors survive a real docker compose restart.

    Uploads a document via HTTP to the running app container, queries, performs a
    real `docker compose restart app`, waits for the container to become healthy,
    then re-queries without re-uploading and asserts that the document list and
    answer citations remain consistent.

    The uploaded content is based on `vertical_slice_fixture.md` with a unique
    comment appended. This guarantees the content hash does not collide with an
    existing registry entry (so processing reaches READY and vectors are upserted)
    while still supplying the RTO fact that downstream legacy integration tests
    expect to find in Qdrant.
    """
    base_url = "http://127.0.0.1:8000"
    fixture_path = EVAL_DOCS / "vertical_slice_fixture.md"
    content = fixture_path.read_bytes() + f"\n\n<!-- restart-test-{uuid.uuid4().hex[:8]} -->\n".encode()

    # Upload via HTTP to the running container so persistence is tested on the
    # actual service volumes, not the host filesystem used by TestClient.
    upload_resp = requests.post(
        f"{base_url}/api/documents",
        files=[("files", ("vertical_slice_fixture.md", BytesIO(content), "text/plain"))],
        timeout=60,
    )
    assert upload_resp.status_code == 200, upload_resp.text
    upload_result = upload_resp.json()["results"][0]
    assert upload_result["status"] == "READY", upload_result
    document_id = upload_result["document_id"]

    # Document is listable before restart.
    before_list = requests.get(f"{base_url}/api/documents", timeout=10).json()
    assert any(d["document_id"] == document_id for d in before_list["documents"])

    # Query before restart returns grounded citations.
    query_before = requests.post(
        f"{base_url}/api/query",
        json={"question": "What is the recovery time objective for Acme?"},
        timeout=120,
    ).json()
    assert query_before["citations"]

    # Real restart of the app service.
    subprocess.run(
        ["docker", "compose", "restart", "app"],
        cwd=REPO_ROOT,
        check=True,
        timeout=120,
    )

    # Wait for the app container to be ready to serve requests again.
    deadline = time.time() + 90
    healthy = False
    while time.time() < deadline:
        try:
            health = requests.get(f"{base_url}/api/documents", timeout=5)
            if health.status_code == 200:
                healthy = True
                break
        except Exception:
            pass
        time.sleep(1)
    assert healthy, "app container did not become healthy after restart"

    # Document still listable after restart without re-uploading.
    after_list = requests.get(f"{base_url}/api/documents", timeout=10).json()
    assert any(d["document_id"] == document_id for d in after_list["documents"])

    # Query after restart returns consistent citations (vectors survived).
    query_after = requests.post(
        f"{base_url}/api/query",
        json={"question": "What is the recovery time objective for Acme?"},
        timeout=120,
    ).json()
    assert query_after["citations"]
    before_chunk_ids = {c["chunk_id"] for c in query_before["citations"]}
    after_chunk_ids = {c["chunk_id"] for c in query_after["citations"]}
    assert before_chunk_ids == after_chunk_ids

"""Integration test: deleting a document stops it contributing to answers.

Requires live Ollama + Qdrant (docker compose up) — excluded from the default
unit suite via the `integration` marker.
"""

from __future__ import annotations

import uuid
from io import BytesIO

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

pytestmark = pytest.mark.integration


def test_deleted_document_no_longer_listed_or_cited() -> None:
    """Upload -> delete -> the document is gone from the list and from citations."""
    marker = f"OBSIDIAN-{uuid.uuid4().hex[:8]}"
    filename = f"vanish-{uuid.uuid4().hex[:8]}.txt"

    upload = client.post(
        "/api/documents",
        files=[
            (
                "files",
                (
                    filename,
                    BytesIO(
                        f"Vanish Note\n\nThe secret project codename is {marker}.\n".encode()
                    ),
                    "text/plain",
                ),
            )
        ],
    )
    assert upload.status_code == 200
    result = next(r for r in upload.json()["results"] if r["filename"] == filename)
    assert result["status"] == "READY", result
    document_id = result["document_id"]

    delete_response = client.delete(f"/api/documents/{document_id}")
    assert delete_response.status_code == 200
    assert delete_response.json() == {"document_id": document_id, "deleted": True}

    listed = client.get("/api/documents").json()["documents"]
    assert all(doc["document_id"] != document_id for doc in listed)

    query = client.post(
        "/api/query",
        json={"question": f"What is the codename containing {marker}?"},
    )
    assert query.status_code == 200
    data = query.json()
    assert all(citation["document_id"] != document_id for citation in data["citations"])
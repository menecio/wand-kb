"""Retrieval configuration, gating, and early-exit tests (AC-12..AC-16, AC-23, AC-24)."""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from qdrant_client.http.models import Distance, VectorParams

from app.config import Settings, settings
from app.main import app
from app.services.qdrant import QdrantClient

client = TestClient(app)


def test_retrieval_settings_are_configurable() -> None:
    """AC-12: top_k, threshold, and context-token budget are configurable via environment."""
    env = {
        "RETRIEVAL_TOP_K": "7",
        "RETRIEVAL_THRESHOLD": "0.55",
        "MAX_CONTEXT_TOKENS": "1024",
    }
    with patch.dict(os.environ, env, clear=False):
        s = Settings()
    assert s.retrieval_top_k == 7
    assert pytest.approx(s.retrieval_threshold) == 0.55
    assert s.max_context_tokens == 1024


def test_default_retrieval_settings_are_sane() -> None:
    """AC-12: Sane defaults exist for retrieval settings."""
    s = Settings()
    assert hasattr(s, "retrieval_top_k")
    assert hasattr(s, "retrieval_threshold")
    assert hasattr(s, "max_context_tokens")
    assert 1 <= s.retrieval_top_k <= 50
    assert 0.0 < s.retrieval_threshold < 1.0
    assert s.max_context_tokens > 0


def test_qdrant_collection_uses_cosine_and_768_dims() -> None:
    """AC-13: Collection creation uses cosine distance and 768 dimensions."""
    qclient = QdrantClient(host="localhost", port=6333)
    mock_client = MagicMock()

    with patch.object(qclient, "_client", mock_client):
        qclient.create_collection(name="kb", dimensions=settings.embedding_dimensions)

    call_kwargs = mock_client.create_collection.call_args.kwargs
    vector_params: VectorParams = call_kwargs["vectors_config"]
    assert vector_params.size == 768
    assert vector_params.distance == Distance.COSINE


def test_identical_fragments_are_deduplicated() -> None:
    """AC-14: Identical chunk text appears only once in the generation context."""
    # This tests the deduplication helper directly if it exists; otherwise it
    # fails until the implementer exposes one.
    try:
        from app.services.query_pipeline import deduplicate_chunks
    except ImportError as exc:  # pragma: no cover
        pytest.fail(f"deduplicate_chunks helper is missing: {exc}")

    chunks = [
        {"id": "a", "text": "duplicate text", "score": 0.9, "metadata": {}},
        {"id": "b", "text": "duplicate text", "score": 0.85, "metadata": {}},
        {"id": "c", "text": "unique text", "score": 0.8, "metadata": {}},
    ]
    deduped = deduplicate_chunks(chunks)
    texts = [c["text"] for c in deduped]
    assert texts.count("duplicate text") == 1
    assert "unique text" in texts


def test_no_fragment_passes_threshold_generation_not_invoked() -> None:
    """AC-23: When all retrieved chunks score below threshold, generation is not called."""
    with (
        patch("app.services.query_pipeline.qdrant_client") as mock_qdrant,
        patch("app.services.query_pipeline.ollama_client") as mock_ollama,
    ):
        mock_qdrant.search.return_value = [
            {
                "id": "chunk-low",
                "score": 0.15,
                "metadata": {
                    "document_id": "doc-1",
                    "source": "low.md",
                    "text": "barely relevant text",
                },
            },
        ]
        mock_ollama.generate_embedding.return_value = [0.1] * settings.embedding_dimensions

        response = client.post("/api/query", json={"question": "What is the RTO?"})

    assert response.status_code == 200
    data = response.json()
    assert data["confidence"] == "INSUFFICIENT_DATA"
    assert data["is_complete"] is False
    assert data["citations"] == []
    # AC-23/D4: generation client was never invoked.
    assert not mock_ollama.generate_structured.called


# ---
# Issue #12 / ADR 0020 (Proposed): recalibrate the gate from 0.55 to 0.50 and
# disclose near-miss scores. See brief.md in .tasks/2026-10-28-retrieval-gating-logging/.
# ---


def test_default_retrieval_threshold_is_0_50(monkeypatch: pytest.MonkeyPatch) -> None:
    """Issue #12: default gate recalibrated from 0.55 to 0.50 (ADR 0020)."""
    monkeypatch.delenv("RETRIEVAL_THRESHOLD", raising=False)
    s = Settings()
    assert pytest.approx(s.retrieval_threshold) == 0.50


def _rto_chunk(score: float) -> dict:
    """Build a retrieved chunk carrying the RTO fact at the given score."""
    return {
        "id": "chunk-1",
        "score": score,
        "metadata": {
            "document_id": "doc-1",
            "source": "dr.md",
            "section": "Disaster Recovery",
            "chunk_index": 0,
            "text": "The recovery time objective is 1 hour.",
        },
    }


def _generation_success() -> MagicMock:
    """A generation-client response that validates against the RTO context chunk."""
    return MagicMock(
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


def test_borderline_score_0_52_passes_gate_and_invokes_generation() -> None:
    """Issue #12: a 0.52 chunk (gated out at 0.55) must reach generation at 0.50."""
    with (
        patch("app.services.query_pipeline.qdrant_client") as mock_qdrant,
        patch("app.services.query_pipeline.ollama_client") as mock_ollama,
    ):
        mock_qdrant.search.return_value = [_rto_chunk(0.52)]
        mock_ollama.generate_embedding.return_value = [0.2] * settings.embedding_dimensions
        mock_ollama.generate_structured.return_value = _generation_success()

        response = client.post(
            "/api/query", json={"question": "What is the recovery time objective?"}
        )

    assert response.status_code == 200
    data = response.json()
    assert data["confidence"] == "HIGH"
    assert data["answer"] == "1 hour"
    assert data["citations"], "generation must be invoked with the borderline chunk"
    assert mock_ollama.generate_structured.called


def test_irrelevant_band_score_0_46_still_gates_out_generation() -> None:
    """Issue #12: the irrelevant band (case_04 scores 0.44-0.46) stays below the 0.50 gate."""
    with (
        patch("app.services.query_pipeline.qdrant_client") as mock_qdrant,
        patch("app.services.query_pipeline.ollama_client") as mock_ollama,
    ):
        mock_qdrant.search.return_value = [_rto_chunk(0.46)]
        mock_ollama.generate_embedding.return_value = [0.2] * settings.embedding_dimensions

        response = client.post(
            "/api/query", json={"question": "What is the recovery time objective?"}
        )

    assert response.status_code == 200
    data = response.json()
    assert data["confidence"] == "INSUFFICIENT_DATA"
    assert data["is_complete"] is False
    assert data["citations"] == []
    assert not mock_ollama.generate_structured.called


def test_gated_response_discloses_near_miss_score_and_threshold() -> None:
    """Issue #12: gated responses disclose the best score and the active threshold."""
    with (
        patch("app.services.query_pipeline.qdrant_client") as mock_qdrant,
        patch("app.services.query_pipeline.ollama_client") as mock_ollama,
    ):
        mock_qdrant.search.return_value = [_rto_chunk(0.47)]
        mock_ollama.generate_embedding.return_value = [0.2] * settings.embedding_dimensions

        response = client.post(
            "/api/query", json={"question": "What is the recovery time objective?"}
        )

    assert response.status_code == 200
    data = response.json()
    assert data["confidence"] == "INSUFFICIENT_DATA"
    assert data["is_complete"] is False
    assert data["citations"] == []
    near_miss = [m for m in data["missing_info"] if "0.47" in m]
    assert near_miss, f"expected near-miss disclosure in missing_info, got: {data['missing_info']}"
    assert any("0.5" in m for m in near_miss), (
        "the near-miss line must also state the active threshold"
    )


def test_gated_response_shape() -> None:
    """AC-24: Gated-out response is INSUFFICIENT_DATA with no factual claims."""
    with (
        patch("app.services.query_pipeline.qdrant_client") as mock_qdrant,
        patch("app.services.query_pipeline.ollama_client") as mock_ollama,
    ):
        mock_qdrant.search.return_value = [
            {
                "id": "chunk-low",
                "score": 0.10,
                "metadata": {
                    "document_id": "doc-1",
                    "source": "low.md",
                    "text": "barely relevant",
                },
            },
        ]
        mock_ollama.generate_embedding.return_value = [0.1] * settings.embedding_dimensions

        response = client.post("/api/query", json={"question": "What is the RTO?"})

    assert response.status_code == 200
    data = response.json()
    assert data["confidence"] == "INSUFFICIENT_DATA"
    assert data["is_complete"] is False
    assert data["citations"] == []
    answer = data["answer"].lower()
    # The answer must not claim the information does not exist.
    assert "does not exist" not in answer
    # It must say evidence was not retrieved.
    assert "evidence" in answer or "retrieved" in answer or "context" in answer
    # Suggestions, if present, remain generic.
    for suggestion in data.get("enrichment_suggestions", []):
        assert suggestion["action_type"] in {"UPLOAD_DOCUMENT", "QUERY_EXTERNAL_SYSTEM", "ASK_USER"}

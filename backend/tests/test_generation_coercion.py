"""Generation-output enum coercion tests (issue #15 / ADR 0021).

The model (qwen2.5:3b) sometimes returns near-miss enum values, e.g.
`"confidence": "NONE"` for questions it is uncertain about. The generation
schema must coerce these to the semantically closest valid value instead of
failing the whole generation. Coercion lives in `_GenerationSchema` only —
the public response models keep strict validation.
"""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.config import settings
from app.main import app
from app.schemas.facet import FacetStatus
from app.schemas.query import ActionType, ConfidenceLevel
from app.services.query_pipeline import _GenerationSchema

client = TestClient(app)


def _schema_with(**overrides: object) -> _GenerationSchema:
    """Build a minimal valid model payload with the given overrides."""
    payload: dict[str, object] = {
        "answer": "Some answer text.",
        "confidence": "HIGH",
        "is_complete": True,
        "missing_info": [],
        "enrichment_suggestions": [],
        "facets": [],
    }
    payload.update(overrides)
    return _GenerationSchema.model_validate_json(json.dumps(payload))


# --- confidence (issue #15: observed live failure was "NONE") -----------------


@pytest.mark.parametrize("raw", ["NONE", "UNKNOWN", "UNSURE", ""])
def test_confidence_aliases_coerce_to_insufficient_data(raw: str) -> None:
    """Issue #15 / AC-1: near-miss confidence values coerce to INSUFFICIENT_DATA."""
    schema = _schema_with(confidence=raw)
    assert schema.confidence == ConfidenceLevel.INSUFFICIENT_DATA


def test_confidence_none_yields_structured_fields_not_error() -> None:
    """Issue #15 / AC-1: coercion preserves the rest of the model payload."""
    schema = _schema_with(
        confidence="NONE",
        is_complete=True,
        missing_info=["Budget approver not named"],
        answer="The approver is not named in the notes.",
    )
    assert schema.confidence == ConfidenceLevel.INSUFFICIENT_DATA
    assert schema.answer == "The approver is not named in the notes."
    assert schema.missing_info == ["Budget approver not named"]


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("high", ConfidenceLevel.HIGH),
        ("Medium", ConfidenceLevel.MEDIUM),
        ("low", ConfidenceLevel.LOW),
        ("insufficient_data", ConfidenceLevel.INSUFFICIENT_DATA),
    ],
)
def test_confidence_is_case_insensitive(raw: str, expected: ConfidenceLevel) -> None:
    """Issue #15 / AC-2: casing must not fail validation."""
    assert _schema_with(confidence=raw).confidence == expected


# --- facet status -------------------------------------------------------------


@pytest.mark.parametrize("raw", ["UNKNOWN", "NONE", "TBD"])
def test_facet_status_unknown_coerces_to_uncertain(raw: str) -> None:
    """Issue #15 / AC-3: unknown facet statuses coerce to UNCERTAIN, facet kept."""
    schema = _schema_with(
        facets=[
            {
                "description": "Budget approver",
                "status": raw,
                "citation_ids": [],
                "associated_gap": None,
            }
        ]
    )
    assert len(schema.facets) == 1
    assert schema.facets[0].status == FacetStatus.UNCERTAIN
    assert schema.facets[0].description == "Budget approver"


def test_facet_status_is_case_insensitive() -> None:
    """Issue #15 / AC-2: 'answered' (lowercase) is accepted; IR-2 still enforced."""
    schema = _schema_with(
        facets=[
            {
                "description": "RTO",
                "status": "answered",
                "citation_ids": ["chunk-1"],
                "associated_gap": None,
            }
        ]
    )
    assert schema.facets[0].status == FacetStatus.ANSWERED


# --- enrichment action_type ---------------------------------------------------


@pytest.mark.parametrize("raw", ["REQUEST_HUMAN", "NONE", "UPLOAD"])
def test_action_type_unknown_coerces_to_ask_user(raw: str) -> None:
    """Issue #15 / AC-3: unknown action types coerce to ASK_USER, suggestion kept."""
    schema = _schema_with(
        enrichment_suggestions=[
            {"action_type": raw, "target": "HR handbook", "reason": "May hold the policy."}
        ]
    )
    assert len(schema.enrichment_suggestions) == 1
    assert schema.enrichment_suggestions[0].action_type == ActionType.ASK_USER
    assert schema.enrichment_suggestions[0].target == "HR handbook"


def test_action_type_is_case_insensitive() -> None:
    """Issue #15 / AC-2: lowercase action types are accepted."""
    schema = _schema_with(
        enrichment_suggestions=[
            {"action_type": "upload_document", "target": "t", "reason": "r"}
        ]
    )
    assert schema.enrichment_suggestions[0].action_type == ActionType.UPLOAD_DOCUMENT


# --- regression guards: valid values pass through unchanged -------------------


@pytest.mark.parametrize(
    "raw", [ConfidenceLevel.HIGH, ConfidenceLevel.MEDIUM, ConfidenceLevel.LOW]
)
def test_valid_confidence_values_pass_through(raw: ConfidenceLevel) -> None:
    """Issue #15 / AC-4: valid enum values are not altered."""
    assert _schema_with(confidence=raw.value).confidence == raw


def test_valid_facet_and_action_values_pass_through() -> None:
    """Issue #15 / AC-4: valid facet statuses and action types are not altered."""
    schema = _schema_with(
        facets=[{"description": "d", "status": "CONFLICTING", "citation_ids": ["c"]}],
        enrichment_suggestions=[
            {"action_type": "QUERY_EXTERNAL_SYSTEM", "target": "t", "reason": "r"}
        ],
    )
    assert schema.facets[0].status == FacetStatus.CONFLICTING
    assert schema.enrichment_suggestions[0].action_type == ActionType.QUERY_EXTERNAL_SYSTEM


# --- end-to-end: the live failure must no longer produce the controlled error -


def test_none_confidence_generation_returns_structured_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Issue #15 / AC-1: a NONE-confidence generation yields the model's answer."""
    raw_model_json = json.dumps(
        {
            "answer": "The approver is not named in the notes.",
            "confidence": "NONE",
            "is_complete": False,
            "missing_info": ["Budget approver not named"],
            "enrichment_suggestions": [],
            "facets": [
                {
                    "description": "Budget approver",
                    "status": "UNKNOWN",
                    "citation_ids": [],
                    "associated_gap": "Approver not named",
                }
            ],
        }
    )

    def fake_generate_structured(model: str, prompt: str, schema: type[BaseModel]) -> object:
        # Mirror the real OllamaClient.generate_structured seam: parse and
        # validate the raw model JSON against the generation schema.
        return schema.model_validate_json(raw_model_json)

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
                    "source": "notes.md",
                    "text": "The budget was approved.",
                },
            },
        ]
        mock_ollama.generate_embedding.return_value = [0.2] * settings.embedding_dimensions
        mock_ollama.generate_structured.side_effect = fake_generate_structured

        response = client.post("/api/query", json={"question": "Who approved the budget?"})

    assert response.status_code == 200
    data = response.json()
    # The controlled-error path would answer "The system could not produce a
    # verified answer: ..."; the model's own text must survive instead.
    assert data["answer"] == "The approver is not named in the notes."
    assert data["confidence"] == "INSUFFICIENT_DATA"
    assert data["is_complete"] is False
    assert data["missing_info"] == ["Budget approver not named"]
    assert len(data["facets"]) == 1
    assert data["facets"][0]["status"] == "UNCERTAIN"
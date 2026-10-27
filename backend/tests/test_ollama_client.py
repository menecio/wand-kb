"""Tests for the Ollama client service."""

from unittest.mock import MagicMock, patch

import pytest
import requests
from pydantic import BaseModel, Field

from app.services.ollama import OllamaClient, OllamaConnectionError


class SampleSchema(BaseModel):
    """Sample schema for structured generation tests."""

    answer: str = Field(..., min_length=1)
    confidence: float = Field(..., ge=0.0, le=1.0)


@pytest.fixture
def ollama_client() -> OllamaClient:
    """Provide an OllamaClient configured for unit tests."""
    return OllamaClient(base_url="http://localhost:11434")


def test_initialization_with_base_url() -> None:
    """OllamaClient stores the provided base URL."""
    client = OllamaClient(base_url="http://ollama:11434")
    assert client.base_url == "http://ollama:11434"


def test_generate_embedding_returns_list_of_floats(ollama_client: OllamaClient) -> None:
    """generate_embedding returns a 768-dimensional vector for nomic-embed-text."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "embedding": [0.1] * 768,
    }

    with patch.object(ollama_client._session, "post", return_value=mock_response) as mock_post:
        embedding = ollama_client.generate_embedding(
            model="nomic-embed-text",
            text="sample query",
        )

    mock_post.assert_called_once()
    assert isinstance(embedding, list)
    assert all(isinstance(value, float) for value in embedding)
    assert len(embedding) == 768


def test_generate_embedding_dimension_matches_model(ollama_client: OllamaClient) -> None:
    """generate_embedding returns exactly 768 floats for nomic-embed-text."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"embedding": [0.42] * 768}

    with patch.object(ollama_client._session, "post", return_value=mock_response):
        result = ollama_client.generate_embedding(
            model="nomic-embed-text",
            text=" Acme RTO",
        )

    assert len(result) == 768


def test_generate_structured_validates_response(ollama_client: OllamaClient) -> None:
    """generate_structured parses and validates JSON against the Pydantic schema."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "message": {
            "content": '{"answer": "1 hour", "confidence": 0.95}',
        },
    }

    with patch.object(ollama_client._session, "post", return_value=mock_response) as mock_post:
        result = ollama_client.generate_structured(
            model="qwen2.5:3b",
            prompt="What is the RTO?",
            schema=SampleSchema,
        )

    mock_post.assert_called_once()
    assert isinstance(result, SampleSchema)
    assert result.answer == "1 hour"
    assert result.confidence == pytest.approx(0.95)


def test_generate_structured_rejects_invalid_payload(ollama_client: OllamaClient) -> None:
    """generate_structured raises a validation error for malformed JSON."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "message": {
            "content": '{"answer": 123, "confidence": "high"}',
        },
    }

    with (
        patch.object(ollama_client._session, "post", return_value=mock_response),
        pytest.raises(Exception),  # noqa: B017
    ):
        ollama_client.generate_structured(
            model="qwen2.5:3b",
            prompt="What is the RTO?",
            schema=SampleSchema,
        )


def test_error_handling_for_connection_failures(ollama_client: OllamaClient) -> None:
    """Connection failures are translated to OllamaConnectionError."""
    with patch.object(
        ollama_client._session,
        "post",
        side_effect=requests.exceptions.ConnectionError("refused"),
    ), pytest.raises(OllamaConnectionError):
        ollama_client.generate_embedding(
            model="nomic-embed-text",
            text="sample",
        )


def test_error_handling_for_timeout(ollama_client: OllamaClient) -> None:
    """Timeout exceptions are translated to OllamaConnectionError."""
    with patch.object(
        ollama_client._session,
        "post",
        side_effect=requests.exceptions.Timeout("timed out"),
    ), pytest.raises(OllamaConnectionError):
        ollama_client.generate_structured(
            model="qwen2.5:3b",
            prompt="What is the RTO?",
            schema=SampleSchema,
        )


@pytest.mark.integration
def test_integration_generate_embedding_from_local_ollama() -> None:
    """Real embedding call against the local Ollama service."""
    client = OllamaClient(base_url="http://localhost:11434")
    embedding = client.generate_embedding(
        model="nomic-embed-text",
        text="Disaster recovery objective",
    )
    assert isinstance(embedding, list)
    assert len(embedding) == 768
    assert all(isinstance(value, float) for value in embedding)


@pytest.mark.integration
def test_integration_generate_structured_from_local_ollama() -> None:
    """Real structured generation call against the local Ollama service."""
    client = OllamaClient(base_url="http://localhost:11434")
    result = client.generate_structured(
        model="qwen2.5:3b",
        prompt="Return JSON with answer '1 hour' and confidence 0.95",
        schema=SampleSchema,
    )
    assert isinstance(result, SampleSchema)
    assert result.answer
    assert 0.0 <= result.confidence <= 1.0

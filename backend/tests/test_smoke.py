"""Smoke tests for external dependencies and configuration.

These tests verify that external services (Ollama, Qdrant) and the FastAPI
application can be reached and behave as expected. Tests that require a running
service are skipped when those prerequisites are not met; they never simulate
successful responses.
"""

import contextlib
import uuid

import pytest
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel, Field
from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse
from qdrant_client.models import Distance, VectorParams

from app.config import Settings, settings
from app.main import app
from app.services.ollama import OllamaClient, OllamaConnectionError

SMOKE_TEST_COLLECTION = "smoke_test_collection"


# -----------------------------------------------------------------------------
# Test 1: Configuration
# -----------------------------------------------------------------------------
def test_config_ollama_defaults():
    """Verify Ollama and Qdrant defaults are configured for local services."""
    explicit_settings = Settings()

    assert explicit_settings.ollama_base_url == "http://ollama:11434"
    assert explicit_settings.ollama_embedding_model == "nomic-embed-text"
    assert explicit_settings.ollama_generation_model == "qwen2.5:3b"
    assert explicit_settings.qdrant_host == "qdrant"
    assert explicit_settings.qdrant_port == 6333
    assert explicit_settings.qdrant_collection_name == "knowledge_base"
    assert explicit_settings.embedding_dimensions == 768


def test_config_env_file_can_load(tmp_path):
    """Verify a .env file can be loaded when present."""
    env_file = tmp_path / ".env"
    env_file.write_text("OLLAMA_BASE_URL=http://custom-ollama:11434\n")

    loaded = Settings(_env_file=str(env_file))
    assert loaded.ollama_base_url == "http://custom-ollama:11434"


# -----------------------------------------------------------------------------
# Test 2: Ollama connectivity
# -----------------------------------------------------------------------------
class SmokeStructuredOutput(BaseModel):
    """Minimal schema for the generative smoke test."""

    test: str = Field(...)


def _ollama_available() -> bool:
    """Return True when the local Ollama service is reachable."""
    client = OllamaClient(base_url=settings.ollama_base_url)
    try:
        client.generate_embedding(model=settings.ollama_embedding_model, text="ping")
        return True
    except OllamaConnectionError:
        return False


@pytest.mark.skipif(not _ollama_available(), reason="Ollama service not reachable")
def test_ollama_embedding_generation():
    """Test embedding generation via the configured local Ollama model."""
    client = OllamaClient(base_url=settings.ollama_base_url)

    embedding = client.generate_embedding(
        model=settings.ollama_embedding_model,
        text="test",
    )

    assert isinstance(embedding, list)
    assert len(embedding) == settings.embedding_dimensions
    assert all(isinstance(value, float) for value in embedding)


@pytest.mark.skipif(not _ollama_available(), reason="Ollama service not reachable")
def test_ollama_structured_output():
    """Test structured output generation via the configured local Ollama model."""
    client = OllamaClient(base_url=settings.ollama_base_url)

    parsed = client.generate_structured(
        model=settings.ollama_generation_model,
        prompt="Return a JSON object with key 'test' and value 'passed'",
        schema=SmokeStructuredOutput,
    )

    assert isinstance(parsed, SmokeStructuredOutput)
    assert parsed.test == "passed"


# -----------------------------------------------------------------------------
# Test 3: Qdrant Collection Operations
# -----------------------------------------------------------------------------
def _qdrant_client() -> QdrantClient:
    """Return a Qdrant client configured from application settings."""
    return QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)


def test_qdrant_collection_operations():
    """Test Qdrant collection create/exist/delete lifecycle."""
    try:
        client = _qdrant_client()
        # Lightweight connectivity/availability check.
        client.get_collections()
    except Exception as exc:  # noqa: BLE001 - we intentionally capture connection errors
        pytest.skip(f"Qdrant unavailable at {settings.qdrant_host}:{settings.qdrant_port}: {exc}")

    collection_name = f"{SMOKE_TEST_COLLECTION}_{uuid.uuid4().hex}"
    vector_size = 128

    try:
        # Create a small test collection.
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )

        # Verify the collection exists.
        collections = client.get_collections()
        assert any(col.name == collection_name for col in collections.collections)

        # Delete the test collection.
        client.delete_collection(collection_name=collection_name)

        # Verify deletion succeeded.
        with pytest.raises(UnexpectedResponse):
            client.get_collection(collection_name=collection_name)
    finally:
        # Best-effort cleanup if the test body left the collection behind.
        with contextlib.suppress(Exception):
            client.delete_collection(collection_name=collection_name)


# -----------------------------------------------------------------------------
# Test 4: FastAPI OpenAPI Generation
# -----------------------------------------------------------------------------
def test_fastapi_openapi_generation():
    """Verify the FastAPI app can generate a complete OpenAPI schema."""
    schema = get_openapi(
        title=app.title,
        version=app.version,
        openapi_version=app.openapi_version,
        description=app.description,
        routes=app.routes,
    )

    assert "paths" in schema
    paths = schema["paths"]
    assert "/api/health" in paths
    assert "/api/documents" in paths
    assert "/api/query" in paths

    components = schema.get("components", {})
    schemas = components.get("schemas", {})

    expected_models = {
        "QueryRequest",
        "QueryResponse",
        "DocumentList",
        "DocumentUploadResult",
        "DocumentSummary",
        "Citation",
        "EnrichmentSuggestion",
    }
    for model_name in expected_models:
        assert model_name in schemas, f"Expected schema {model_name} not found in OpenAPI spec"

    expected_enums = {
        "ConfidenceLevel",
        "DocumentStatus",
        "ActionType",
    }
    for enum_name in expected_enums:
        assert enum_name in schemas, f"Expected enum {enum_name} not found in OpenAPI spec"

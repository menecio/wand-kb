"""Smoke tests for external dependencies and configuration.

These tests verify that external services (OpenAI, Qdrant) and the FastAPI
application can be reached and behave as expected. Tests that require real
credentials or a running service are skipped when those prerequisites are not
met; they never simulate successful responses.
"""

import contextlib
import uuid

import pytest
from fastapi.openapi.utils import get_openapi
from openai import AsyncOpenAI, OpenAIError
from pydantic import BaseModel, Field, SecretStr
from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse
from qdrant_client.models import Distance, VectorParams

from app.config import Settings, settings
from app.main import app

SMOKE_TEST_COLLECTION = "smoke_test_collection"


def _has_openai_key() -> bool:
    """Return True when a non-empty OpenAI API key is configured."""
    return settings.openai_api_key is not None and settings.openai_api_key.get_secret_value() != ""


# -----------------------------------------------------------------------------
# Test 1: Configuration Security
# -----------------------------------------------------------------------------
def test_config_no_secret_exposure():
    """Verify API key is not exposed in string representations and is optional."""
    explicit_settings = Settings()

    # API key must be optional and stored as a secret type.
    annotation = Settings.model_fields["openai_api_key"].annotation
    assert annotation == SecretStr | None

    # If a key is configured, it must not appear in repr/str/dict exports.
    if explicit_settings.openai_api_key:
        secret_value = explicit_settings.openai_api_key.get_secret_value()
        assert secret_value not in repr(explicit_settings)
        assert secret_value not in str(explicit_settings)
        assert secret_value not in str(explicit_settings.model_dump())

    # An unset key should be falsy and not cause validation failures.
    unset_settings = Settings(openai_api_key=None)
    assert unset_settings.openai_api_key is None


def test_config_env_file_can_load(tmp_path):
    """Verify a .env file can be loaded when present."""
    env_file = tmp_path / ".env"
    env_file.write_text("OPENAI_API_KEY=sk-test-key-from-env-file\n")

    loaded = Settings(_env_file=str(env_file))
    assert loaded.openai_api_key is not None
    assert loaded.openai_api_key.get_secret_value() == "sk-test-key-from-env-file"

    # Confirm the loaded key does not leak through repr.
    assert loaded.openai_api_key.get_secret_value() not in repr(loaded)


# -----------------------------------------------------------------------------
# Test 2: Embedding Generation
# -----------------------------------------------------------------------------
@pytest.mark.skipif(not _has_openai_key(), reason="OPENAI_API_KEY not configured")
def test_embedding_generation():
    """Test embedding generation via the configured OpenAI model."""
    client = AsyncOpenAI(api_key=settings.openai_api_key.get_secret_value())

    try:
        response = client.embeddings.create(
            model=settings.embedding_model,
            input="test",
        )
        embedding = response.data[0].embedding
    except OpenAIError as exc:
        pytest.fail(f"OpenAI embedding request failed: {exc}")

    assert isinstance(embedding, list)
    assert len(embedding) == settings.embedding_dimensions
    assert all(isinstance(value, float) for value in embedding)


# -----------------------------------------------------------------------------
# Test 3: Generative Model Structured Output
# -----------------------------------------------------------------------------
class SmokeStructuredOutput(BaseModel):
    """Minimal schema for the generative smoke test."""

    test: str = Field(...)


@pytest.mark.skipif(not _has_openai_key(), reason="OPENAI_API_KEY not configured")
def test_generative_model_structured_output():
    """Test structured output generation via the configured OpenAI model."""
    client = AsyncOpenAI(api_key=settings.openai_api_key.get_secret_value())

    try:
        completion = client.beta.chat.completions.parse(
            model=settings.generation_model,
            messages=[
                {
                    "role": "user",
                    "content": "Return a JSON object with key 'test' and value 'passed'",
                }
            ],
            response_format=SmokeStructuredOutput,
        )
        parsed = completion.choices[0].message.parsed
    except OpenAIError as exc:
        pytest.fail(f"OpenAI structured output request failed: {exc}")

    assert isinstance(parsed, SmokeStructuredOutput)
    assert parsed.test == "passed"


# -----------------------------------------------------------------------------
# Test 4: Qdrant Collection Operations
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
# Test 5: FastAPI OpenAPI Generation
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

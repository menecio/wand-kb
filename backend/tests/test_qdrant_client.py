"""Tests for the Qdrant vector-store client."""

from unittest.mock import MagicMock, patch

import pytest
from qdrant_client.http.models import Distance, VectorParams

from app.services.qdrant import QdrantClient, QdrantConnectionError


@pytest.fixture
def qdrant_client() -> QdrantClient:
    """Provide a QdrantClient configured for unit tests."""
    return QdrantClient(host="localhost", port=6333)


def test_initialization_with_host_and_port() -> None:
    """QdrantClient stores the provided host and port."""
    client = QdrantClient(host="qdrant", port=6333)
    assert client.host == "qdrant"
    assert client.port == 6333


def test_create_collection_uses_cosine_distance(qdrant_client: QdrantClient) -> None:
    """create_collection creates a collection with cosine distance and the given dimension."""
    mock_client = MagicMock()

    with patch.object(qdrant_client, "_client", mock_client):
        qdrant_client.create_collection(name="test_collection", dimensions=768)

    mock_client.create_collection.assert_called_once()
    call_kwargs = mock_client.create_collection.call_args.kwargs
    assert call_kwargs["collection_name"] == "test_collection"
    vector_params = call_kwargs["vectors_config"]
    assert isinstance(vector_params, VectorParams)
    assert vector_params.size == 768
    assert vector_params.distance == Distance.COSINE


def test_upsert_points_batches_payloads(qdrant_client: QdrantClient) -> None:
    """upsert_points forwards points to the underlying Qdrant client."""
    mock_client = MagicMock()
    points = [
        {
            "id": "chunk-1",
            "vector": [0.1] * 768,
            "payload": {"source": "doc.md", "chunk_index": 0},
        },
        {
            "id": "chunk-2",
            "vector": [0.2] * 768,
            "payload": {"source": "doc.md", "chunk_index": 1},
        },
    ]

    with patch.object(qdrant_client, "_client", mock_client):
        qdrant_client.upsert_points(collection_name="kb", points=points)

    mock_client.upsert.assert_called_once()
    call_args = mock_client.upsert.call_args.kwargs
    assert call_args["collection_name"] == "kb"
    assert len(call_args["points"]) == 2


def test_search_returns_scored_results(qdrant_client: QdrantClient) -> None:
    """search returns a list of scored chunks."""
    mock_client = MagicMock()
    mock_client.search.return_value = [
        MagicMock(
            id="chunk-1",
            score=0.95,
            payload={"source": "doc.md", "section": "DR", "chunk_index": 0},
        ),
        MagicMock(
            id="chunk-2",
            score=0.87,
            payload={"source": "doc.md", "section": "DR", "chunk_index": 1},
        ),
    ]
    query_vector = [0.1] * 768

    with patch.object(qdrant_client, "_client", mock_client):
        results = qdrant_client.search(
            collection_name="kb",
            query_vector=query_vector,
            limit=5,
        )

    mock_client.search.assert_called_once()
    call_kwargs = mock_client.search.call_args.kwargs
    assert call_kwargs["collection_name"] == "kb"
    assert call_kwargs["query_vector"] == query_vector
    assert call_kwargs["limit"] == 5
    assert len(results) == 2
    assert results[0]["id"] == "chunk-1"
    assert results[0]["score"] == pytest.approx(0.95)
    assert results[1]["id"] == "chunk-2"


def test_search_returns_empty_list_when_no_matches(qdrant_client: QdrantClient) -> None:
    """search returns an empty list when Qdrant finds nothing."""
    mock_client = MagicMock()
    mock_client.search.return_value = []

    with patch.object(qdrant_client, "_client", mock_client):
        results = qdrant_client.search(
            collection_name="kb",
            query_vector=[0.0] * 768,
            limit=3,
        )

    assert results == []


def test_error_handling_for_connection_failures(qdrant_client: QdrantClient) -> None:
    """Connection failures are raised as QdrantConnectionError."""
    with patch.object(
        qdrant_client._client,
        "create_collection",
        side_effect=Exception("Connection refused"),
    ), pytest.raises(QdrantConnectionError):
        qdrant_client.create_collection(name="kb", dimensions=768)


@pytest.mark.integration
def test_integration_create_collection() -> None:
    """Create a collection against a real local Qdrant instance."""
    client = QdrantClient(host="localhost", port=6333)
    client.create_collection(name="integration_test", dimensions=768)
    collections = client._client.get_collections().collections
    assert any(c.name == "integration_test" for c in collections)


@pytest.mark.integration
def test_integration_upsert_and_search() -> None:
    """Upsert and search against a real local Qdrant instance."""
    client = QdrantClient(host="localhost", port=6333)
    client.create_collection(name="integration_test", dimensions=768)
    points = [
        {
            "id": "chunk-1",
            "vector": [1.0] + [0.0] * 767,
            "payload": {"source": "doc.md", "chunk_index": 0},
        },
    ]
    client.upsert_points(collection_name="integration_test", points=points)
    results = client.search(
        collection_name="integration_test",
        query_vector=[1.0] + [0.0] * 767,
        limit=1,
    )
    assert len(results) == 1
    assert results[0]["id"] == "chunk-1"

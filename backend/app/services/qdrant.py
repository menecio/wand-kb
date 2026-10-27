"""Qdrant vector-store client wrapper."""

import uuid
from typing import Any

from qdrant_client import QdrantClient as _QdrantClient
from qdrant_client.http.models import Distance, PointStruct, VectorParams


class QdrantConnectionError(Exception):
    """Raised when Qdrant cannot be reached."""


_ID_NAMESPACE = uuid.UUID("a7f7c6e5-1b2c-4d3e-8f4a-9b5c6d7e8f9a")


def _is_valid_qdrant_id(value: Any) -> bool:
    """Return True if value is a Qdrant-compatible point id."""
    if isinstance(value, int):
        return value >= 0
    if isinstance(value, str):
        try:
            int(value)
            return int(value) >= 0
        except ValueError:
            pass
        try:
            uuid.UUID(value)
            return True
        except ValueError:
            return False
    return False


def _normalize_qdrant_id(value: Any) -> tuple[Any, str | None]:
    """Return a Qdrant-compatible id plus an optional original-id payload key."""
    if _is_valid_qdrant_id(value):
        return value, None
    original = str(value)
    return uuid.uuid5(_ID_NAMESPACE, original), original


class QdrantClient:
    """Thin wrapper around the official Qdrant client."""

    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port
        self._client = _QdrantClient(host=host, port=port)

    def create_collection(self, name: str, dimensions: int) -> None:
        """Create a collection configured with cosine distance (idempotent)."""
        try:
            self._client.create_collection(
                collection_name=name,
                vectors_config=VectorParams(size=dimensions, distance=Distance.COSINE),
            )
        except Exception as exc:
            # Treat an already-existing collection as success.
            if "already exists" in str(exc).lower():
                return
            raise QdrantConnectionError(f"Failed to create Qdrant collection {name}: {exc}") from exc

    def ensure_collection(self, name: str, dimensions: int) -> None:
        """Create the collection only if it does not already exist."""
        try:
            collections = self._client.get_collections().collections
            if any(c.name == name for c in collections):
                return
        except Exception as exc:
            raise QdrantConnectionError(f"Failed to list Qdrant collections: {exc}") from exc

        self.create_collection(name=name, dimensions=dimensions)

    def upsert_points(self, collection_name: str, points: list[dict]) -> None:
        """Upsert points into the named collection."""
        try:
            qdrant_points = []
            for point in points:
                point_id, original_id = _normalize_qdrant_id(point["id"])
                payload = dict(point.get("payload", {}))
                if original_id is not None:
                    payload["original_id"] = original_id
                qdrant_points.append(
                    PointStruct(
                        id=point_id,
                        vector=point["vector"],
                        payload=payload,
                    )
                )
            self._client.upsert(collection_name=collection_name, points=qdrant_points)
        except Exception as exc:
            raise QdrantConnectionError(f"Failed to upsert points into {collection_name}: {exc}") from exc

    def search(
        self,
        collection_name: str,
        query_vector: list[float],
        limit: int = 5,
    ) -> list[dict]:
        """Search the collection and return scored payloads."""
        try:
            query_results = self._client.query_points(
                collection_name=collection_name,
                query=query_vector,
                limit=limit,
                with_payload=True,
            )
            points = query_results.points
            # Defensive fallback for tests/mocks that do not model query_points correctly.
            if callable(points):
                raise AttributeError("query_points result does not expose points")
        except Exception:
            try:
                points = self._client.search(  # type: ignore[attr-defined]
                    collection_name=collection_name,
                    query_vector=query_vector,
                    limit=limit,
                    with_payload=True,
                )
            except Exception as fallback_exc:
                raise QdrantConnectionError(
                    f"Failed to search Qdrant collection {collection_name}: {fallback_exc}"
                ) from fallback_exc

        return [
            {
                "id": (result.payload or {}).get("original_id", result.id),
                "score": result.score,
                "metadata": result.payload or {},
            }
            for result in points
        ]

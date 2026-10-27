"""Qdrant vector-store client wrapper."""

from qdrant_client import QdrantClient as _QdrantClient
from qdrant_client.http.models import Distance, PointStruct, VectorParams


class QdrantConnectionError(Exception):
    """Raised when Qdrant cannot be reached."""


class QdrantClient:
    """Thin wrapper around the official Qdrant client."""

    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port
        self._client = _QdrantClient(host=host, port=port)

    def create_collection(self, name: str, dimensions: int) -> None:
        """Create a collection configured with cosine distance."""
        try:
            self._client.create_collection(
                collection_name=name,
                vectors_config=VectorParams(size=dimensions, distance=Distance.COSINE),
            )
        except Exception as exc:
            raise QdrantConnectionError(f"Failed to create Qdrant collection {name}: {exc}") from exc

    def upsert_points(self, collection_name: str, points: list[dict]) -> None:
        """Upsert points into the named collection."""
        try:
            qdrant_points = [
                PointStruct(
                    id=point["id"],
                    vector=point["vector"],
                    payload=point.get("payload", {}),
                )
                for point in points
            ]
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
            results = self._client.search(  # type: ignore[attr-defined]
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit,
                with_payload=True,
            )
        except Exception as exc:
            raise QdrantConnectionError(f"Failed to search Qdrant collection {collection_name}: {exc}") from exc

        return [
            {
                "id": result.id,
                "score": result.score,
                "metadata": result.payload or {},
            }
            for result in results
        ]

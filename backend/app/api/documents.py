"""Document upload and listing endpoints."""

from __future__ import annotations

import asyncio
import hashlib
import logging
import shutil
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.config import settings
from app.schemas.document import (
    DocumentDeleteResponse,
    DocumentList,
    DocumentStatus,
    DocumentSummary,
    DocumentUploadResult,
    UploadResultItem,
)
from app.services.document_processing import chunk_text, extract_text
from app.services.ollama import OllamaClient
from app.services.qdrant import QdrantClient, QdrantConnectionError
from app.services.registry import load_registry, save_registry

router = APIRouter()

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".pdf", ".md", ".txt"}

def _get_documents() -> dict[str, DocumentSummary]:
    """Load the document registry from disk into DocumentSummary instances."""
    raw = load_registry()
    documents: dict[str, DocumentSummary] = {}
    for document_id, item in raw.items():
        try:
            documents[document_id] = DocumentSummary.model_validate(item)
        except Exception:
            continue
    return documents


def _persist_documents(documents: dict[str, DocumentSummary]) -> None:
    """Persist the current registry to disk."""
    raw = {document_id: summary.model_dump(mode="json") for document_id, summary in documents.items()}
    save_registry(raw)


def _ensure_upload_dir() -> Path:
    """Create and return the configured upload directory."""
    upload_dir = Path(settings.upload_dir).resolve()
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir


def _compute_sha256(data: bytes) -> str:
    """Return the SHA-256 hex digest of the provided bytes."""
    return hashlib.sha256(data).hexdigest()


def _save_uploaded_file(upload_dir: Path, document_id: str, filename: str, data: bytes) -> Path:
    """Persist the uploaded bytes under the document's storage folder."""
    document_dir = upload_dir / document_id
    document_dir.mkdir(parents=True, exist_ok=True)
    file_path = document_dir / filename
    file_path.write_bytes(data)
    return file_path


def _find_duplicate_document(
    documents: dict[str, DocumentSummary], content_sha256: str
) -> DocumentSummary | None:
    """Return an existing READY document with the same content hash, if any."""
    for summary in documents.values():
        if summary.content_sha256 == content_sha256 and summary.status == DocumentStatus.READY:
            return summary
    return None


def _process_uploaded_file(file_path: Path, document_id: str, filename: str, content_sha256: str) -> None:
    """Extract text, chunk, embed, and store vectors for a single document."""
    ollama_client = OllamaClient(base_url=settings.ollama_base_url)
    qdrant_client = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)

    raw_text = extract_text(file_path)

    chunks = chunk_text(
        raw_text,
        chunk_size=settings.chunk_size,
        overlap=settings.chunk_overlap,
        source=filename,
    )

    points: list[dict[str, Any]] = []
    for chunk in chunks:
        embedding = ollama_client.generate_embedding(
            model=settings.ollama_embedding_model,
            text=chunk["text"],
        )
        points.append(
            {
                "id": chunk["id"],
                "vector": embedding,
                "payload": {
                    "document_id": document_id,
                    "source": filename,
                    "section": chunk["metadata"].get("section"),
                    "chunk_index": chunk["metadata"].get("chunk_index"),
                    "text": chunk["text"],
                },
            }
        )

    if points:
        qdrant_client.ensure_collection(
            name=settings.qdrant_collection_name,
            dimensions=settings.embedding_dimensions,
        )
        qdrant_client.upsert_points(
            collection_name=settings.qdrant_collection_name,
            points=points,
        )
    logger.info(
        "document processed: %s, %d chunks stored",
        filename,
        len(points),
    )


@router.get("/api/documents", response_model=DocumentList)
async def list_documents() -> DocumentList:
    """List all uploaded documents."""
    return DocumentList(documents=list(_get_documents().values()))


@router.post("/api/documents", response_model=DocumentUploadResult)
async def upload_documents(
    files: Annotated[list[UploadFile], File(...)],
) -> DocumentUploadResult:
    """Upload multiple documents for processing."""
    results: list[UploadResultItem] = []
    upload_dir = _ensure_upload_dir()
    documents = _get_documents()

    for file in files:
        filename = file.filename or "unknown"

        # Reject unsupported file types up front.
        if not any(filename.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS):
            results.append(
                UploadResultItem(
                    filename=filename,
                    status=DocumentStatus.REJECTED,
                    document_id=None,
                    error="Unsupported file type",
                )
            )
            continue

        data = await file.read()
        content_sha256 = _compute_sha256(data)

        # Idempotency: identical bytes reuse the existing READY document.
        existing = _find_duplicate_document(documents, content_sha256)
        if existing is not None:
            results.append(
                UploadResultItem(
                    filename=filename,
                    status=DocumentStatus.DUPLICATE,
                    document_id=existing.document_id,
                    error=None,
                )
            )
            continue

        document_id = str(uuid.uuid4())
        documents[document_id] = DocumentSummary(
            document_id=document_id,
            document_name=filename,
            content_sha256=content_sha256,
            status=DocumentStatus.PROCESSING,
            created_at=datetime.now(UTC),
        )

        error_message: str | None = None
        try:
            file_path = _save_uploaded_file(upload_dir, document_id, filename, data)
            await asyncio.to_thread(
                _process_uploaded_file,
                file_path,
                document_id,
                filename,
                content_sha256,
            )
            documents[document_id].status = DocumentStatus.READY
        except Exception as exc:
            error_message = str(exc) or "Processing failed"
            documents[document_id].status = DocumentStatus.FAILED
            documents[document_id].error = error_message

        summary = documents[document_id]
        results.append(
            UploadResultItem(
                filename=filename,
                status=summary.status,
                document_id=document_id,
                error=error_message,
            )
        )

    _persist_documents(documents)
    return DocumentUploadResult(results=results)


@router.delete("/api/documents/{document_id}", response_model=DocumentDeleteResponse)
def delete_document(document_id: str) -> DocumentDeleteResponse:
    """Hard-delete a document from the filesystem, registry and vector store.

    Qdrant is cleared first: if the vector store is unreachable the request
    fails and the document stays intact everywhere (ADR-0020, no partial
    state). Filesystem and registry cleanup follow only after that succeeded.
    """
    documents = _get_documents()
    if document_id not in documents:
        raise HTTPException(status_code=404, detail=f"Document {document_id} not found")

    qdrant_client = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)
    try:
        qdrant_client.delete_document_points(
            settings.qdrant_collection_name, document_id
        )
    except QdrantConnectionError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    document_dir = _ensure_upload_dir() / document_id
    if document_dir.exists():
        shutil.rmtree(document_dir)

    del documents[document_id]
    _persist_documents(documents)
    return DocumentDeleteResponse(document_id=document_id, deleted=True)

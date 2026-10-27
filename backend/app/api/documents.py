"""Document upload and listing endpoints."""

import asyncio
import hashlib
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, File, UploadFile

from app.config import settings
from app.schemas.document import DocumentList, DocumentStatus, DocumentSummary, DocumentUploadResult
from app.services.document_processing import chunk_text, extract_text
from app.services.ollama import OllamaClient
from app.services.qdrant import QdrantClient

router = APIRouter()

ALLOWED_EXTENSIONS = {".pdf", ".md", ".txt"}

_documents: dict[str, DocumentSummary] = {}


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
                "id": f"{document_id}:{chunk['id']}",
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
        qdrant_client.upsert_points(
            collection_name=settings.qdrant_collection_name,
            points=points,
        )

    summary = _documents[document_id]
    summary.status = DocumentStatus.READY
    summary.content_sha256 = content_sha256


@router.get("/api/documents", response_model=DocumentList)
async def list_documents() -> DocumentList:
    """List all uploaded documents."""
    return DocumentList(documents=list(_documents.values()))


@router.post("/api/documents", response_model=DocumentUploadResult)
async def upload_documents(
    files: Annotated[list[UploadFile], File(...)],
) -> DocumentUploadResult:
    """Upload multiple documents for processing."""
    accepted: list[str] = []
    rejected: list[str] = []
    upload_dir = _ensure_upload_dir()

    for file in files:
        filename = file.filename or "unknown"
        if not any(filename.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS):
            rejected.append(filename)
            continue

        accepted.append(filename)
        data = await file.read()
        document_id = str(uuid.uuid4())
        content_sha256 = _compute_sha256(data)

        _documents[document_id] = DocumentSummary(
            document_id=document_id,
            document_name=filename,
            content_sha256=content_sha256,
            status=DocumentStatus.PROCESSING,
            created_at=datetime.now(UTC),
        )

        try:
            file_path = _save_uploaded_file(upload_dir, document_id, filename, data)
            await asyncio.to_thread(
                _process_uploaded_file,
                file_path,
                document_id,
                filename,
                content_sha256,
            )
        except Exception:
            summary = _documents[document_id]
            summary.status = DocumentStatus.FAILED
            summary.error = "Processing failed"

    return DocumentUploadResult(accepted=accepted, rejected=rejected)

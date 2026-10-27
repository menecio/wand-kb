from typing import Annotated

from fastapi import APIRouter, File, UploadFile

from ..schemas.document import DocumentList, DocumentUploadResult

router = APIRouter()

ALLOWED_EXTENSIONS = {".pdf", ".md", ".txt"}


@router.get("/api/documents", response_model=DocumentList)
async def list_documents() -> DocumentList:
    """List all uploaded documents."""
    return DocumentList(documents=[])


@router.post("/api/documents", response_model=DocumentUploadResult)
async def upload_documents(
    files: Annotated[list[UploadFile], File(...)],
) -> DocumentUploadResult:
    """Upload multiple documents for processing."""
    accepted: list[str] = []
    rejected: list[str] = []

    for file in files:
        filename = file.filename or "unknown"
        if any(filename.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS):
            accepted.append(filename)
        else:
            rejected.append(filename)

    return DocumentUploadResult(accepted=accepted, rejected=rejected)

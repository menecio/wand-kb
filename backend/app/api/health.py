from fastapi import APIRouter

from app.config import settings

router = APIRouter()


@router.get("/api/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {
        "status": "ok",
        "version": "0.1.0",
        "ollama_configured": bool(settings.ollama_base_url),
        "qdrant_configured": bool(
            settings.qdrant_host and settings.qdrant_port and settings.qdrant_collection_name
        ),
    }

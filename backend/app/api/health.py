from fastapi import APIRouter

from app.config import settings

router = APIRouter()


@router.get("/api/health")
async def health_check() -> dict:
    """Health check endpoint."""
    openai_configured = (
        settings.openai_api_key is not None
        and settings.openai_api_key.get_secret_value() != ""
    )
    return {
        "status": "ok",
        "version": "0.1.0",
        "openai_configured": openai_configured,
        "qdrant_configured": bool(
            settings.qdrant_host and settings.qdrant_port and settings.qdrant_collection_name
        ),
    }

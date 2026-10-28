import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api import documents, health, query

app = FastAPI(
    title="Knowledge Base Search & Enrichment",
    description="AI-powered document search and answer generation with enrichment suggestions",
    version="0.1.0",
)


@app.exception_handler(RequestValidationError)
async def _validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Return a controlled 422 response without stack traces."""
    return JSONResponse(status_code=422, content={"detail": "Invalid request"})


app.include_router(health.router)
app.include_router(documents.router)
app.include_router(query.router)

# Serve the built React app from the same origin. Routers above take precedence
# for /api/*, /docs, and /openapi.json; this mount falls back to static assets.
_frontend_dist = Path(os.getenv("FRONTEND_DIST_DIR", "frontend/dist")).resolve()
if (_frontend_dist / "index.html").exists():
    app.mount("/", StaticFiles(directory=_frontend_dist, html=True), name="frontend")

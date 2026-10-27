## [2026-10-27T00:00] implementer — Task 3 endpoint implementation

### Files modified (backend)

- `backend/app/main.py`
  - Registered `health`, `documents`, and `query` routers.
  - Added CORS middleware for `http://localhost:5173`.
  - Removed unused imports.
- `backend/app/api/health.py`
  - Implemented `GET /api/health` returning `status`, `version`, `openai_configured`, and `qdrant_configured`.
- `backend/app/api/documents.py`
  - Implemented `GET /api/documents` returning `{ "documents": [] }`.
  - Implemented `POST /api/documents` with multipart `files` uploads and case-insensitive extension validation (`.pdf`, `.md`, `.txt`), returning `{ "accepted": [...], "rejected": [...] }`.
- `backend/app/api/query.py`
  - Kept `POST /api/query` stub returning `QueryResponse` with `INSUFFICIENT_DATA` confidence.
- `backend/app/schemas/document.py`
  - Added `DocumentList` and `DocumentUploadResult` response schemas.
  - Modernized type annotations while preserving behavior.
- `backend/app/schemas/__init__.py`
  - Exported new document schemas.
- `backend/app/config.py`, `backend/app/schemas/facet.py`, `backend/app/schemas/query.py`
  - Minor modernization (import ordering, `StrEnum`, `X | None`, future annotations) to satisfy `ruff check app` without changing behavior.

### Verification

- `uv run ruff check app` — passed
- `uv run ruff format --check app` — passed
- `uv run mypy app` — passed
- `uv run pytest -q` — 35 passed
- FastAPI (`uvicorn app.main:app`) starts cleanly.
- Manual endpoint checks:
  - `GET /api/health` returns expected status and configuration flags.
  - `GET /api/documents` returns `{ "documents": [] }`.
  - `POST /api/query` returns stub response with `INSUFFICIENT_DATA`.
  - `POST /api/documents` accepts `.pdf`/`.md` and rejects `.exe`.
- OpenAPI docs are generated automatically at `/docs`.

### Notes / issues

- `ruff check app tests` still reports pre-existing lint/style warnings in `tests/test_models.py` and `tests/test_validation.py` (import ordering, unused imports, blind `Exception` catches). I did not modify tests per the implementer contract.

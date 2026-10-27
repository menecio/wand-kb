# Task 3 Specification: API Endpoints and OpenAPI

## Objective
Create functional stubs for all API endpoints without implementing actual business logic.

## Endpoints to Implement

### 1. GET /api/health
- Returns basic status and configuration checks
- Response format:
```json
{
  "status": "ok",
  "version": "0.1.0",
  "openai_configured": true,
  "qdrant_configured": true
}
```
- `openai_configured`: true if OPENAI_API_KEY is set
- `qdrant_configured`: true if Qdrant settings are valid

### 2. GET /api/documents
- Returns list of DocumentSummary objects
- Response format:
```json
{
  "documents": []
}
```
- Currently returns empty list (no documents ingested yet)

### 3. POST /api/documents
- Accepts multiple file uploads (PDF, Markdown, TXT)
- Request: multipart/form-data with `files` field
- Response format:
```json
{
  "accepted": ["file1.pdf", "file2.md"],
  "rejected": []
}
```
- Currently accepts all files without processing
- Validates file extensions: .pdf, .md, .txt
- Files with invalid extensions go to `rejected`

### 4. POST /api/query
- Accepts QueryRequest
- Returns QueryResponse (stub with INSUFFICIENT_DATA)
- Response format:
```json
{
  "answer": "RAG pipeline not yet implemented",
  "confidence": "INSUFFICIENT_DATA",
  "is_complete": false,
  "missing_info": ["Full RAG pipeline implementation"],
  "enrichment_suggestions": [],
  "citations": []
}
```

## Implementation Requirements

1. Update `backend/app/main.py` to include routers
2. Create/update router files in `backend/app/api/`:
   - `health.py`: health check endpoint
   - `documents.py`: document listing and upload endpoints
   - `query.py`: query endpoint
3. All endpoints should be functional stubs (no actual business logic)
4. Enable CORS middleware for frontend development
5. Generate OpenAPI documentation automatically

## CORS Configuration
Add CORS middleware in `main.py`:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## File Validation
For POST /api/documents, validate file extensions:
- Allowed: .pdf, .md, .txt
- Check filename extension (case-insensitive)
- Files with invalid extensions should be in `rejected` list

## Verification Steps

1. Start FastAPI server:
```bash
cd backend
uv run uvicorn app.main:app --reload
```

2. Check endpoints:
```bash
# Health check
curl http://localhost:8000/api/health

# List documents
curl http://localhost:8000/api/documents

# OpenAPI documentation
open http://localhost:8000/docs
```

3. Verify OpenAPI spec:
- All 4 endpoints appear in Swagger UI
- Request/response schemas are correct
- Enums are properly documented

4. Test file upload (should accept all files):
```bash
curl -X POST http://localhost:8000/api/documents \
  -F "files=@test.pdf" \
  -F "files=@test.md"
```

5. Test query endpoint:
```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the capital of France?"}'
```

## Acceptance Criteria

- [ ] All 4 endpoints are functional
- [ ] FastAPI starts without errors
- [ ] OpenAPI documentation is accessible at /docs
- [ ] Health endpoint returns correct status
- [ ] Documents endpoint returns empty list
- [ ] File upload accepts valid extensions
- [ ] File upload rejects invalid extensions
- [ ] Query endpoint returns stub response with INSUFFICIENT_DATA
- [ ] CORS middleware is configured
- [ ] All existing tests still pass (35 tests total)

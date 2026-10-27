# Phase 1 — Project Initialization

## Objective
Initialize the project, freeze the contracts, prepare a minimal evaluation dataset, and verify external dependencies.

## Scope
- Project structure setup
- Data contracts definition
- API endpoint stubs
- Evaluation dataset preparation
- Smoke tests for external dependencies

## Out of scope
- RAG pipeline implementation
- User interface implementation
- Full document ingestion
- Actual retrieval and generation

## Acceptance criteria
1. Repository initialized with proper structure
2. Dependencies configured
3. Data contracts defined and validated
4. API stubs respond correctly
5. Evaluation dataset prepared (10+ cases)
6. External dependencies verified or blockers documented

## Architecture decisions (already made)
- Local, single-user application
- Backend: Python 3.14, FastAPI, Pydantic v2
- Persistent local Qdrant
- PyMuPDF for text-based PDFs
- React, TypeScript, Vite, shadcn/ui for frontend (later)
- FastAPI on 127.0.0.1
- No authentication
- No CORS (Vite proxy for dev, FastAPI serves production)
- API key from environment variables only
- Supported documents: PDF, Markdown, TXT
- Out of scope: OCR, auto-enrichment, hybrid search, reranking, auth, cloud
- Rating not part of baseline

## Phase 1 Completion Review

### Completed Tasks
1. ✅ Task 1: Project structure initialized (25+ files created)
2. ✅ Task 2: Data contracts defined with Pydantic models (13 models, 28 validation tests)
3. ✅ Task 3: API endpoint stubs implemented (4 endpoints, OpenAPI docs)
4. ✅ Task 4: Evaluation dataset prepared (10 cases, 3 synthetic documents)
5. ✅ Task 5: Smoke tests completed (3 passed, 3 blocked - external dependencies)

### Phase 1 Checklist
- [x] Repository initialized with proper structure
- [x] Dependencies configured (FastAPI, Pydantic, OpenAI, Qdrant, PyMuPDF)
- [x] Data contracts defined and validated
- [x] API stubs respond correctly
- [x] Evaluation dataset prepared (10 cases)
- [x] External dependencies verified or blockers documented

### Known Issues
- OpenAI API key not configured (embedding and generation tests blocked)
- Qdrant server not running (vector store tests blocked)
- These are expected and documented; Phase 2 will require actual configuration

### Phase 2 Entry Point
Phase 2 (Functional Vertical Slice) can now begin with:
- Document ingestion pipeline implementation
- Embedding generation (requires OPENAI_API_KEY)
- Vector storage in Qdrant (requires Qdrant server)
- Retrieval and generation logic
- Integration with evaluation dataset

The foundation is solid and ready for functional implementation.

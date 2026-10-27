# Knowledge Base Search & Enrichment

AI-powered document search and answer generation system with enrichment suggestions.

## Overview

This system allows users to:
- Upload multiple documents (PDF, Markdown, TXT)
- Search documents using natural language questions
- Receive AI-generated answers based on document content
- Identify when information is missing or uncertain
- Get suggestions for enriching the knowledge base

## Architecture

### Technology Stack

**Backend:**
- Python 3.14
- FastAPI (web framework)
- Pydantic v2 (data validation)
- OpenAI API (embeddings and generation)
- Qdrant (vector database)
- PyMuPDF (PDF processing)

**Frontend (planned):**
- React
- TypeScript
- Vite
- shadcn/ui

### Design Decisions

- **Local, single-user application**: No authentication required
- **No CORS configuration**: Vite proxy for development, FastAPI serves production build
- **Environment-based configuration**: API keys loaded from `.env` file
- **Structured output**: JSON responses with answer, confidence, missing_info
- **Text-based PDFs only**: OCR is out of scope
- **No cloud deployment**: Local prototype only

### Supported Document Types

- PDF (text-based, no OCR)
- Markdown (.md)
- Plain text (.txt)

### Out of Scope

- OCR for image-based PDFs
- Auto-enrichment from external sources
- Hybrid search (combining vector and keyword search)
- Reranking
- Authentication and authorization
- Cloud deployment
- Answer quality rating (baseline scope)

## Project Structure

```
wand-take-home/
├── backend/                # Backend API and services
│   ├── app/
│   │   ├── api/           # FastAPI routers
│   │   ├── schemas/       # Pydantic models
│   │   ├── services/      # Business logic
│   │   ├── config.py      # Configuration
│   │   └── main.py        # FastAPI application
│   ├── tests/             # Backend tests
│   ├── requirements.txt   # Python dependencies
│   └── pyproject.toml     # Project configuration
├── frontend/              # Frontend application (to be implemented)
├── eval/                  # Evaluation dataset
│   ├── documents/         # Sample documents
│   └── cases/             # Evaluation test cases
├── data/                  # Local data storage (gitignored)
│   └── qdrant/           # Qdrant vector database
├── .env.example           # Environment variables template
└── README.md              # This file
```

## Configuration

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Add your OpenAI API key to `.env`:
   ```
   OPENAI_API_KEY=your-actual-api-key
   ```

3. Optional: Configure other settings in `.env` (see `.env.example` for options)

## External Dependencies

This application requires:

- **OpenAI API**: For generating embeddings and LLM responses
- **Qdrant**: Local vector database (will be set up automatically)

## Installation

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
cd backend
pip install -r requirements.txt
```

## Running the Application

```bash
# Start the backend server
cd backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The API will be available at `http://127.0.0.1:8000`

API documentation: `http://127.0.0.1:8000/docs`

## Current Status

**Phase 1 — Project Initialization: COMPLETE** ✅

Completed tasks:
- ✅ Project structure initialized (25+ files created)
- ✅ Data contracts defined with Pydantic models (13 models, 28 validation tests passing)
- ✅ API endpoint stubs implemented (4 endpoints, OpenAPI docs generated)
- ✅ Evaluation dataset prepared (10 test cases, 3 synthetic documents)
- ✅ Smoke tests completed (3 passed, 3 blocked - external dependencies)

**Test Coverage:** 38 tests passing, 3 skipped (external dependencies)

**Next Steps:**
- Implement document ingestion pipeline (PDF, Markdown, TXT parsing)
- Implement embedding generation with OpenAI API
- Implement vector storage in Qdrant
- Implement retrieval and generation logic
- Connect all components end-to-end
- Build frontend interface

## Known Issues

### Blocked Smoke Tests (Expected)
The following smoke tests are blocked until external dependencies are configured:
- **OpenAI API tests**: Requires `OPENAI_API_KEY` environment variable
  - Test embedding generation
  - Test generative structured output
- **Qdrant tests**: Requires Qdrant server running at `localhost:6333`
  - Test collection operations

These blocks are documented and expected. Phase 2 implementation will require:
1. Setting `OPENAI_API_KEY` in `.env` file
2. Starting Qdrant: `docker run -p 6333:6333 qdrant/qdrant`

All local tests (configuration, API endpoints, data validation) are passing.

## License

Private repository - Wand AI take-home challenge

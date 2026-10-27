# Task 1 Specification: Project Structure and Initialization

## Objective
Create the initial project structure, configuration files, and README for the Knowledge Base Search & Enrichment prototype.

## Worktree Location
`/Users/menecio/.local/share/opencode/worktree/global/phase1-init`

## Files to Create

### 1. Backend Application Structure

#### backend/app/__init__.py
```python
# Backend application package
```

#### backend/app/main.py
```python
from fastapi import FastAPI

app = FastAPI(
    title="Knowledge Base Search & Enrichment",
    description="AI-powered document search and answer generation with enrichment suggestions",
    version="0.1.0"
)

# Include routers here as they are created
# from .api import health, documents, query
# app.include_router(health.router)
# app.include_router(documents.router)
# app.include_router(query.router)
```

#### backend/app/config.py
```python
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Keys
    openai_api_key: Optional[str] = None
    
    # Qdrant configuration
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection_name: str = "knowledge_base"
    
    # Embedding model
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536
    
    # Generation model
    generation_model: str = "gpt-4o-mini"
    
    # Chunking configuration
    chunk_size: int = 1000
    chunk_overlap: int = 200
    
    # Server configuration
    host: str = "127.0.0.1"
    port: int = 8000
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
```

#### backend/app/schemas/__init__.py
```python
# Pydantic models for request/response schemas
```

#### backend/app/schemas/query.py
```python
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

class ConfidenceLevel(str, Enum):
    """Confidence levels for answer quality."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"

class ActionType(str, Enum):
    """Types of enrichment actions."""
    UPLOAD_DOCUMENT = "UPLOAD_DOCUMENT"
    QUERY_EXTERNAL_SYSTEM = "QUERY_EXTERNAL_SYSTEM"
    ASK_USER = "ASK_USER"

class Citation(BaseModel):
    """A citation referencing a specific chunk of a document."""
    chunk_id: str
    document_id: str
    document_name: str
    page_start: Optional[int] = None
    page_end: Optional[int] = None
    section: Optional[str] = None
    excerpt: str
    relevance_score: float = Field(ge=0.0, le=1.0)

class EnrichmentSuggestion(BaseModel):
    """A suggestion for enriching the knowledge base."""
    action_type: ActionType
    target: str
    reason: str
    suggested_query: Optional[str] = None

class QueryRequest(BaseModel):
    """Request model for querying the knowledge base."""
    question: str = Field(..., min_length=1, max_length=10000)

class QueryResponse(BaseModel):
    """Response model for knowledge base queries."""
    response_id: str
    answer: str
    confidence: ConfidenceLevel
    is_complete: bool
    missing_info: List[str]
    enrichment_suggestions: List[EnrichmentSuggestion]
    citations: List[Citation]
```

#### backend/app/schemas/document.py
```python
from pydantic import BaseModel
from typing import Optional
from enum import Enum
from datetime import datetime

class DocumentStatus(str, Enum):
    """Status of document processing."""
    PROCESSING = "PROCESSING"
    READY = "READY"
    FAILED = "FAILED"

class DocumentSummary(BaseModel):
    """Summary of an uploaded document."""
    document_id: str
    document_name: str
    content_sha256: str
    status: DocumentStatus
    error: Optional[str] = None
    created_at: datetime
```

#### backend/app/schemas/facet.py
```python
from pydantic import BaseModel
from typing import List, Optional
from enum import Enum

class FacetStatus(str, Enum):
    """Status of a question facet."""
    ANSWERED = "ANSWERED"
    PARTIAL = "PARTIAL"
    MISSING = "MISSING"
    UNCERTAIN = "UNCERTAIN"
    CONFLICTING = "CONFLICTING"

class Facet(BaseModel):
    """Internal representation of a question facet for LLM output."""
    description: str
    status: FacetStatus
    citation_ids: List[str]
    associated_gap: Optional[str] = None
```

#### backend/app/api/__init__.py
```python
# API routers
```

#### backend/app/api/health.py
```python
from fastapi import APIRouter

router = APIRouter()

@router.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "knowledge-base-api"
    }
```

#### backend/app/api/documents.py
```python
from fastapi import APIRouter, UploadFile, File
from typing import List
from ..schemas.document import DocumentSummary

router = APIRouter()

@router.get("/api/documents", response_model=List[DocumentSummary])
async def list_documents():
    """List all uploaded documents."""
    # TODO: Implement document retrieval
    return []

@router.post("/api/documents")
async def upload_documents(files: List[UploadFile] = File(...)):
    """Upload multiple documents for processing."""
    # TODO: Implement document upload and processing
    results = []
    for file in files:
        results.append({
            "filename": file.filename,
            "status": "received",
            "message": "Document processing not yet implemented"
        })
    return {"results": results}
```

#### backend/app/api/query.py
```python
from fastapi import APIRouter
from ..schemas.query import QueryRequest, QueryResponse, ConfidenceLevel
import uuid

router = APIRouter()

@router.post("/api/query", response_model=QueryResponse)
async def query_knowledge_base(request: QueryRequest):
    """Query the knowledge base with a natural language question."""
    # TODO: Implement RAG pipeline
    # This is a stub that returns an INSUFFICIENT_DATA response
    return QueryResponse(
        response_id=str(uuid.uuid4()),
        answer="RAG pipeline not yet implemented",
        confidence=ConfidenceLevel.INSUFFICIENT_DATA,
        is_complete=False,
        missing_info=["Full RAG pipeline implementation"],
        enrichment_suggestions=[],
        citations=[]
    )
```

#### backend/app/services/__init__.py
```python
# Service layer for business logic
```

#### backend/tests/__init__.py
```python
# Backend tests
```

#### backend/tests/test_models.py
```python
"""Tests for Pydantic models."""
import pytest
from datetime import datetime
from app.schemas.query import (
    QueryRequest, QueryResponse, ConfidenceLevel, 
    Citation, EnrichmentSuggestion, ActionType
)
from app.schemas.document import DocumentSummary, DocumentStatus
from app.schemas.facet import Facet, FacetStatus

def test_query_request_valid():
    """Test valid QueryRequest."""
    request = QueryRequest(question="What is the capital of France?")
    assert request.question == "What is the capital of France?"

def test_query_request_empty_question():
    """Test QueryRequest with empty question raises validation error."""
    with pytest.raises(Exception):
        QueryRequest(question="")

def test_citation_valid():
    """Test valid Citation."""
    citation = Citation(
        chunk_id="chunk_123",
        document_id="doc_456",
        document_name="test.pdf",
        page_start=1,
        page_end=2,
        section="Introduction",
        excerpt="This is a test excerpt",
        relevance_score=0.95
    )
    assert citation.chunk_id == "chunk_123"
    assert citation.relevance_score == 0.95

def test_citation_invalid_score():
    """Test Citation with invalid relevance_score."""
    with pytest.raises(Exception):
        Citation(
            chunk_id="chunk_123",
            document_id="doc_456",
            document_name="test.pdf",
            excerpt="Test",
            relevance_score=1.5
        )

def test_enrichment_suggestion():
    """Test EnrichmentSuggestion."""
    suggestion = EnrichmentSuggestion(
        action_type=ActionType.UPLOAD_DOCUMENT,
        target="Financial report Q4 2024",
        reason="Missing financial data",
        suggested_query="Q4 2024 revenue"
    )
    assert suggestion.action_type == ActionType.UPLOAD_DOCUMENT

def test_document_summary():
    """Test DocumentSummary."""
    doc = DocumentSummary(
        document_id="doc_123",
        document_name="test.pdf",
        content_sha256="abc123",
        status=DocumentStatus.READY,
        created_at=datetime.now()
    )
    assert doc.status == DocumentStatus.READY

def test_facet():
    """Test Facet model."""
    facet = Facet(
        description="What is the revenue?",
        status=FacetStatus.ANSWERED,
        citation_ids=["chunk_1", "chunk_2"]
    )
    assert facet.status == FacetStatus.ANSWERED
    assert len(facet.citation_ids) == 2
```

### 2. Configuration Files

#### backend/requirements.txt
```
# Core dependencies
fastapi>=0.115.0
pydantic>=2.10.0
pydantic-settings>=2.6.0
uvicorn[standard]>=0.32.0
python-multipart>=0.0.12

# LLM and embeddings
openai>=1.54.0

# Vector database
qdrant-client>=1.12.0

# Document processing
pymupdf>=1.24.0
markdown>=3.7

# Utilities
python-dotenv>=1.0.1
```

#### backend/pyproject.toml
```toml
[project]
name = "wand-knowledge-base"
version = "0.1.0"
description = "AI-powered knowledge base search and enrichment"
requires-python = ">=3.14"
dependencies = [
    "fastapi>=0.115.0",
    "pydantic>=2.10.0",
    "pydantic-settings>=2.6.0",
    "uvicorn[standard]>=0.32.0",
    "python-multipart>=0.0.12",
    "openai>=1.54.0",
    "qdrant-client>=1.12.0",
    "pymupdf>=1.24.0",
    "markdown>=3.7",
    "python-dotenv>=1.0.1",
]

[dependency-groups]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.24.0",
    "httpx>=0.27.0",
    "ruff>=0.6",
    "mypy>=1.11",
]

[tool.ruff]
line-length = 100
target-version = "py314"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "SIM"]
ignore = ["E501"]

[tool.mypy]
python_version = "3.14"
strict = false
warn_unused_configs = true
ignore_missing_imports = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
asyncio_mode = "auto"
```

#### .env.example
```
# OpenAI API Key (required for embeddings and generation)
OPENAI_API_KEY=your-openai-api-key-here

# Qdrant configuration (optional, defaults shown)
# QDRANT_HOST=localhost
# QDRANT_PORT=6333
# QDRANT_COLLECTION_NAME=knowledge_base

# Embedding model configuration (optional)
# EMBEDDING_MODEL=text-embedding-3-small
# EMBEDDING_DIMENSIONS=1536

# Generation model configuration (optional)
# GENERATION_MODEL=gpt-4o-mini

# Chunking configuration (optional)
# CHUNK_SIZE=1000
# CHUNK_OVERLAP=200

# Server configuration (optional)
# HOST=127.0.0.1
# PORT=8000
```

#### .gitignore (append to existing)
Append the following to the existing .gitignore file:
```
# Qdrant local storage
data/
*.db
*.sqlite

# Project-specific
.env.local
.env.*.local
```

Note: The existing .gitignore already covers most Python, Node, and IDE patterns. Only append the Qdrant storage and local env patterns.

### 3. Frontend Directory

Create an empty `frontend/` directory with a placeholder file:

#### frontend/.gitkeep
```
# Frontend application directory (to be implemented in later phase)
```

### 4. Evaluation Directory

#### eval/documents/.gitkeep
```
# Sample documents for evaluation
```

#### eval/cases/.gitkeep
```
# Evaluation test cases
```

### 5. Data Directory

#### data/.gitkeep
```
# Local data storage (gitignored)
# Qdrant vector database will be stored here
```

### 6. README.md

```markdown
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

**Phase 1 Complete:**
- ✅ Project structure initialized
- ✅ Data contracts defined (Pydantic models)
- ✅ API endpoint stubs created
- ⏳ Evaluation dataset (in progress)
- ⏳ Smoke tests (pending)

**Next Steps:**
- Implement document ingestion pipeline
- Implement RAG retrieval and generation
- Build frontend interface

## Known Issues

None at this time.

## License

Private repository - Wand AI take-home challenge
```

## Verification Steps

After creating all files, verify:
1. All files exist in the correct locations
2. Python files have valid syntax (no import errors)
3. .env and .env.local are excluded from .gitignore
4. README.md reflects the actual scope and architecture
5. Directory structure matches the specification

## Important Notes

- Do NOT implement any RAG pipeline logic
- Do NOT create React components
- Do NOT implement actual document processing
- All API endpoints should return stub responses
- All Pydantic models should be complete and valid
- Focus on structure and contracts, not functionality

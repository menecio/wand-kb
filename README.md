# Knowledge Base Search & Enrichment

Local, AI-powered document search and answer generation with enrichment suggestions.

## Overview

This system allows users to:

- Upload multiple documents (PDF, Markdown, TXT)
- Search documents using natural language questions
- Receive AI-generated answers grounded in the retrieved document content
- Identify when information is missing or uncertain
- Get suggestions for enriching the knowledge base

All AI processing runs locally via Ollama. No external AI provider or API key is used.

## Technology Stack

- **Backend:** Python 3.14, FastAPI, Pydantic v2
- **Embeddings:** Ollama `nomic-embed-text` (768 dimensions)
- **Generation:** Ollama `qwen2.5:3b`
- **Vector store:** Qdrant (cosine distance, 768 dimensions)
- **PDF processing:** PyMuPDF
- **Runtime:** Docker Compose

## Architecture Decisions

- **Local-only AI:** No external AI APIs, no API keys, no fallback providers.
- **No authentication or CORS:** Single-user local prototype.
- **Environment-based configuration:** Settings loaded from environment variables.
- **Structured JSON output:** `answer`, `confidence`, `is_complete`, `missing_info`, `citations`, `facets`.
- **Text-based PDFs only:** OCR is out of scope.
- **No cloud deployment:** Local prototype only.

## Supported Document Types

- PDF (text-based, no OCR)
- Markdown (.md)
- Plain text (.txt)

## Out of Scope

- OCR for image-based PDFs
- Auto-enrichment from external sources
- Hybrid search or reranking
- Authentication and authorization
- Cloud deployment
- Answer quality rating
- Frontend development (this phase)

## Project Structure

```
wand-take-home/
├── backend/                # Backend API and services
│   ├── app/               # FastAPI application
│   │   ├── api/          # FastAPI routers
│   │   ├── schemas/      # Pydantic models
│   │   ├── services/     # Business logic
│   │   ├── config.py     # Configuration
│   │   └── main.py       # FastAPI application entry point
│   ├── tests/            # Backend tests
│   ├── docs/             # Data-contract integrity rules
│   ├── pyproject.toml    # Project configuration
│   └── uv.lock           # Dependency lock file
├── eval/                  # Evaluation dataset and runner
│   ├── documents/        # Sample documents
│   ├── cases.json        # Evaluation cases
│   ├── run_eval.py       # Evaluation runner
│   ├── CALIBRATION.md    # Threshold calibration notes
│   └── RESULTS.md        # Observed evaluation results
├── docker-compose.yml    # Compose stack
└── README.md             # This file
```

## Configuration

All configuration is via environment variables (loaded by `backend/app/config.py`):

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_BASE_URL` | `http://ollama:11434` | Ollama API URL |
| `OLLAMA_EMBEDDING_MODEL` | `nomic-embed-text` | Embedding model |
| `OLLAMA_GENERATION_MODEL` | `qwen2.5:3b` | Generation model |
| `QDRANT_HOST` | `qdrant` | Qdrant host |
| `QDRANT_PORT` | `6333` | Qdrant port |
| `QDRANT_COLLECTION_NAME` | `knowledge_base` | Vector collection name |
| `EMBEDDING_DIMENSIONS` | `768` | Must match `nomic-embed-text` |
| `CHUNK_SIZE` | `1000` | Chunk size in words |
| `CHUNK_OVERLAP` | `200` | Chunk overlap in words |
| `UPLOAD_DIR` | `data/uploads` | Document storage |
| `REGISTRY_PATH` | `data/registry.json` | Document registry JSON file |
| `RETRIEVAL_TOP_K` | `5` | Number of chunks retrieved |
| `RETRIEVAL_THRESHOLD` | `0.55` | Minimum cosine similarity to pass the gate |
| `MAX_CONTEXT_TOKENS` | `2048` | Estimated token budget for generation context |

## Running the Application

```bash
docker compose up -d
```

This starts:

- `app` on http://127.0.0.1:8000
- `qdrant` on http://127.0.0.1:6333
- `ollama` on http://127.0.0.1:11434
- `ollama-init` pulls `nomic-embed-text` and `qwen2.5:3b` once into a persistent volume

API documentation is available at http://127.0.0.1:8000/docs.

## Retrieval and Thresholding

Retrieval uses dense vector search in Qdrant with cosine similarity. The pipeline:

1. Embed the question with `nomic-embed-text`.
2. Retrieve `RETRIEVAL_TOP_K` chunks.
3. Deduplicate identical fragment texts, keeping the highest score.
4. Apply `MAX_CONTEXT_TOKENS` budget.
5. Gate: only chunks with cosine similarity >= `RETRIEVAL_THRESHOLD` are passed to generation.
6. If no chunk passes the threshold, generation is skipped and a structured `INSUFFICIENT_DATA` response is returned.

The chosen threshold and observed false rejections/acceptances are documented in `eval/CALIBRATION.md`.

## Confidence Rubric

- **HIGH:** The answer is directly and unambiguously supported by the retrieved evidence.
- **MEDIUM:** The evidence supports the answer but a material facet remains partially covered or ambiguous.
- **LOW:** The evidence is weak, tangential, or the answer is uncertain.
- **INSUFFICIENT_DATA:** No fragment passed the relevance threshold; generation was not invoked.

There is no `confidence_score`; confidence is qualitative only.

## Completeness Semantics

- `is_complete=True` only when all material facets are answered and no material gaps or conflicts remain. `missing_info` must be empty and no facet may be `MISSING`, `UNCERTAIN`, or `CONFLICTING`.
- `is_complete=False` when evidence is partial, ambiguous, conflicting, or missing.
- `INSUFFICIENT_DATA` confidence always implies `is_complete=False`.

## Known Limitations

- **Local model latency:** First generation call can be slow while the model loads into memory; subsequent calls are faster.
- **Structured-output quality:** `qwen2.5:3b` sometimes returns malformed JSON or violates the facet/citation contract. The backend applies one bounded retry and returns a controlled `INSUFFICIENT_DATA` error if validation still fails.
- **Dense retrieval only:** No hybrid search, reranking, or OCR. Queries that need keyword matching or image-based PDFs will fail.
- **Single-process registry:** The JSON registry is suitable for a single-user prototype; concurrent writers are not supported.
- **Embedding quality:** Small embedding shifts can cause answerable questions to gate out or irrelevant fragments to pass. Calibration is documented in `eval/CALIBRATION.md`.
- **Evaluation case_08:** "Are there any conflicts in the documents?" gates out (`INSUFFICIENT_DATA`) because dense retrieval does not match this global/meta question strongly enough to pass the 0.55 threshold.
- **Evaluation case_03:** "What are the company policies and what products do we sell?" retrieves borderline fragments but the model returns `is_complete=False` because product information is missing from the context.
- **Evaluation case_11:** "What is the recovery time objective for Acme production systems?" still returns `is_complete=True` despite the presence of contradictory 1-hour and 4-hour documents, because the model cites only the 1-hour sources and the backend conflict detector inspects only cited excerpts.
- **Post-fix deltas:** The most recent evaluation run also recorded incomplete classifications for case_01 (multiple vacation-policy versions in the KB), case_06 (model number missing from the spec sheet), and case_10 (budget approver not explicitly named). See `eval/CALIBRATION.md` and `eval/RESULTS.md` for full per-case observations.
- **Conflict-detection scope:** The deterministic backend conflict check (ADR 0016) handles the numeric-contradiction class for the same facet's cited excerpts (e.g., "1 hour" vs "4 hours"). Non-numeric conflicts, semantic equivalences (e.g., "1 hour" vs "60 minutes"), and conflicts excluded from the model's citations remain model-dependent.

## Running Tests

Unit tests (no real inference):

```bash
cd backend
rm -rf data/*
uv run pytest -m 'not integration' --tb=short -q
```

Integration tests (require `docker compose up -d`):

```bash
cd backend
uv run pytest -m integration --tb=short -q
```

> **Note:** The unit tests assume a clean `backend/data/` directory. Leftover registry/uploads from previous runs can cause duplicate-detection failures.

## Evaluation

After starting the stack:

```bash
uv run python eval/run_eval.py
```

Results are written to `eval/RESULTS.md`.

## License

Private repository - Wand AI take-home challenge

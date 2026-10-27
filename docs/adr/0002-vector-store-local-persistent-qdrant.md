# 0002. Vector store: local persistent Qdrant

- Status: Proposed
- Date: 2026-10-27
- Context: The RAG pipeline needs a vector store that persists across process restarts on a single machine, supports metadata filtering for citations, and runs locally without cloud accounts. In-memory state would lose indexed documents on restart and force re-ingestion.
- Decision: Use a local, persistent Qdrant instance (Docker, `localhost:6333`, on-disk storage under `data/qdrant/`) as the vector store.
- Alternatives considered:
  - In-memory FAISS — rejected because it does not persist by default and would require custom serialization/reload logic, plus no metadata filtering out of the box.
  - Chroma — rejected because its embedded/server modes and persistence semantics are less predictable for a long-lived local service, and Qdrant offers stronger filtering/payload support.
  - pgvector (PostgreSQL) — rejected because it introduces a Postgres dependency and migration overhead disproportionate to a single-user prototype.
- Consequences: Persistent, filterable vector search with a simple HTTP API. Trade-off: requires running a Qdrant server (Docker) during development and tests; smoke tests for it are blocked until the server is up.
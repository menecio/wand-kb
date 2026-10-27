# 0009. Embeddings via OpenAI

- Status: Proposed
- Date: 2026-10-27
- Context: The RAG pipeline needs text embeddings for retrieval and a generative model for structured answers (`answer`, `confidence`, `missing_info`). Using one provider for both reduces integration surface and leverages high-quality, maintained models. A local embedding model would add heavy dependencies and hardware requirements.
- Decision: Use OpenAI for embeddings (`text-embedding-3-small`, 1536 dims) and generation (`gpt-4o-mini` with structured outputs).
- Alternatives considered:
  - Local embedding models (sentence-transformers) — rejected because they add large dependencies, require model downloads/GPU for good throughput, and lower retrieval quality versus OpenAI.
  - Other cloud providers (Cohere/Voyage/Anthropic) — rejected because mixing providers increases cost and integration complexity; OpenAI already covers generation with structured outputs.
  - OpenAI larger embedding models — rejected because `text-embedding-3-small` balances cost/quality for a prototype; can upgrade later if eval shows need.
- Consequences: High-quality embeddings and structured generation with one SDK. Trade-off: requires `OPENAI_API_KEY` and network access; incurs API cost; smoke tests for embeddings are blocked until the key is set.
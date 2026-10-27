# 0011. Local models via Ollama for embeddings and generation

- Status: Accepted
- Date: 2026-10-27
- Context: The challenge requires all AI processing to be local, with no external AI APIs or fallback. ADR 0009 (Proposed) chose OpenAI embeddings (`text-embedding-3-small`, 1536 dims) and generation (`gpt-4o-mini`), which contradicts the local-only reality of the starting environment (an `ollama` service already runs `nomic-embed-text` and `qwen2.5:3b`). The Qdrant collection dimensions and the backend client must match the chosen local embedding model.
- Decision: Use Ollama for both embeddings (`nomic-embed-text`, 768 dimensions) and structured generation (`qwen2.5:3b`), invoked through the Ollama HTTP API from the backend. No external AI provider or fallback exists anywhere in the system. This ADR supersedes ADR 0009 upon user acceptance (ADR 0009's Status is left untouched by this draft).
- Alternatives considered:
  - OpenAI (as in ADR 0009) — rejected because it violates the local-only constraint, requires an API key and network access, incurs cost, and contradicts the challenge's "no external AI APIs" rule.
  - In-process sentence-transformers — rejected because it adds heavy ML dependencies and model-download/GPU concerns, duplicating the Ollama service already provisioned in compose and diverging from the runtime's model-persistence setup.
  - Other local runtimes (llama.cpp, vLLM) — rejected because Ollama is already in compose with persistent model storage and a simple HTTP API; switching runtimes adds infrastructure for no benefit.
  - Larger local models (e.g. `qwen2.5:7b`) — rejected because the 3b model balances latency and quality on CPU within the ~2.5h budget; upgrade remains an option if evaluation shows need.
- Consequences: No external keys or network dependency; models persist in the `ollama_data` volume and are not re-downloaded. The Qdrant collection must be created at 768 dimensions with cosine distance, and documents/queries must share `nomic-embed-text`. Trade-off: smaller-model quality and latency limits must be recorded in evaluation evidence rather than hidden.
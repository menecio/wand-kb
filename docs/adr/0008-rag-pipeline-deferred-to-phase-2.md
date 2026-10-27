# 0008. RAG pipeline deferred to Phase 2; Phase 1 only scaffolding

- Status: Proposed
- Date: 2026-10-27
- Context: Phase 1 scope is project initialization: structure, contracts, API stubs, evaluation dataset, and dependency smoke tests. Implementing ingestion, embedding, retrieval, and generation in the same phase would conflate scaffolding with feature work, obscure contract validation, and risk untested code before external dependencies (OpenAI, Qdrant) are verified.
- Decision: Phase 1 delivers structure, Pydantic contracts, endpoint stubs, evaluation dataset, and smoke tests only. Full RAG pipeline (ingestion, embedding, storage, retrieval, generation) is implemented in Phase 2.
- Alternatives considered:
  - Full implementation in Phase 1 — rejected because it would skip contract-first validation, mix concerns, and ship unverified integration code before dependencies are configured.
  - Parallel scaffolding + partial RAG — rejected because partial pipelines cannot be meaningfully tested and would muddy acceptance criteria.
- Consequences: Clean separation of contracts vs. implementation; Phase 1 is independently verifiable. Trade-off: no end-to-end answer capability until Phase 2; external dependency blockers are documented rather than resolved.
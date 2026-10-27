# 0001. Backend stack: Python 3.14 + FastAPI + Pydantic v2

- Status: Proposed
- Date: 2026-10-27
- Context: The prototype is a local, single-user knowledge-base search service that must expose a typed HTTP API, validate request/response payloads, and integrate with ML libraries (OpenAI, Qdrant, PyMuPDF). A lightweight, async-capable framework with first-class schema validation and auto-generated OpenAPI docs is needed to keep scaffolding small and iteration fast.
- Decision: Use Python 3.14 with FastAPI as the web framework and Pydantic v2 for all request/response schemas and settings.
- Alternatives considered:
  - Django — rejected because its ORM, admin, and batteries-included stack add weight and indirection not needed for a single-user prototype, slowing scaffolding.
  - Flask — rejected because it lacks built-in validation and OpenAPI generation, requiring extra extensions and boilerplate for the typed contracts we want.
  - Node/Express (TypeScript) — rejected because the ML/PDF/vector ecosystem (OpenAI SDK, PyMuPDF, Qdrant client) is strongest in Python, and mixing runtimes would add friction.
- Consequences: FastAPI gives async endpoints and auto-generated `/docs`; Pydantic v2 gives fast, strict validation and `SecretStr` for keys. Trade-off: Python 3.14 is cutting-edge, so some third-party wheels may lag; pin versions and verify in CI.
# 0004. Single-user, no authentication

- Status: Proposed
- Date: 2026-10-27
- Context: The challenge targets a local prototype for evaluation, not a multi-tenant SaaS. Adding authentication, session management, and user-scoped data would expand scope without improving the core RAG/search acceptance criteria, and would complicate testing.
- Decision: Build a single-user application with no authentication or authorization; the backend binds to 127.0.0.1 and trusts the local caller.
- Alternatives considered:
  - JWT/session-based auth — rejected because it adds user management, token lifecycle, and secured endpoints that the challenge does not require.
  - Multi-tenant data isolation — rejected because it multiplies storage and query complexity for no evaluation benefit.
  - API-key-on-requests auth — rejected because it still implies multiple callers and secret distribution, unnecessary for a local single-user tool.
- Consequences: Simpler code and tests, faster iteration. Trade-off: must never be exposed to a network or shared; if multi-user support is later needed, a new ADR must supersede this one.
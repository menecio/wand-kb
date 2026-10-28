# Report — test-writer, iteration 1

## [2026-10-28T10:25] test-writer — failing tests written and committed

Files created:

- `backend/tests/test_api_document_delete.py` — 4 endpoint tests (mocked
  Ollama/Qdrant, `temp_upload_dir` isolation): AC-1 (delete clears filesystem
  + registry + Qdrant, 200 + `{"document_id","deleted"}`), AC-2 (not listed
  after delete), AC-3 (unknown id → 404, detail mentions "document", no
  Qdrant call), no-partial-state (Qdrant failure → 503, file+registry
  intact), any-status (READY/FAILED/PROCESSING incl. registry row without a
  file on disk).
- `backend/tests/test_integration_document_delete.py` — 1 `integration`-marked
  test (live Ollama/Qdrant): upload → delete → not listed → query returns no
  citation with the deleted document_id.
- `frontend/src/App.delete.test.tsx` — 3 vitest tests: labelled trash button
  per row (accessible name `Delete <name>`), click → `DELETE /api/documents/{id}`
  + row removed without reload + success notice ("<name> deleted"), failure →
  `alert` notice + row remains.
- `frontend/e2e/delete-document.spec.ts` — Playwright journey: upload via UI,
  click `Delete <name>`, row disappears, no error alert.

Criterion → test map:

- AC-1 (stores cleared, 200+JSON): `test_delete_removes_file_registry_and_qdrant_points`
- AC-2 (not listed / not cited): same test + `test_integration_document_delete.py`
- AC-3 (unknown id 404): `test_delete_unknown_document_returns_404_and_changes_nothing`
- No-partial-state refinement: `test_delete_failure_keeps_document_intact`
- Any-status decision: `test_delete_works_for_failed_and_processing_documents`
- UI criteria 4–6: `App.delete.test.tsx` (3 tests) + e2e spec
- AC-7 (suites/lint green after implementation): verified in later phases

Contract seams defined by these tests (implementation must satisfy them):

- `QdrantClient.delete_document_points(collection_name, document_id)` —
  raises `QdrantConnectionError` on failure.
- Frontend button accessible name: `Delete <document_name>`.
- After a successful delete the list is updated from state (no refetch);
  success notice contains "<name> deleted"; failure notice has role `alert`.

TDD red state (verified before any implementation):

- `cd backend && uv run pytest -m "not integration"` → **4 failed** (new),
  122 passed, 3 skipped — no regressions.
- `cd frontend && npx vitest run` → **3 failed** (new), 24 passed — no
  regressions. (`npm ci` run first to populate the fresh worktree's
  node_modules.)
- Lint/typecheck on test files: ruff, mypy, tsc, eslint all clean.

Commit: `8977561` — `test(api): add failing delete-document tests for endpoint and UI contract`

Notes:

- The unknown-id 404 test asserts the error detail mentions "document", so it
  genuinely fails against the absent route (generic FastAPI 404).
- Playwright e2e requires the compose stack; it is part of the contract but
  exercised by visual verification / on demand, not by the vitest unit suite.

# Report — implementer, iteration 1

## [2026-10-28T10:40] implementer — delete feature implemented, tests green, committed

Backend:

- `app/services/qdrant.py`: new `delete_document_points(collection_name,
  document_id)` — deletes all points via `FilterSelector` on payload
  `document_id`; wraps failures in `QdrantConnectionError`.
- `app/api/documents.py`: new `DELETE /api/documents/{document_id}` — 404
  (detail names the document) for unknown ids; Qdrant deletion FIRST so a
  vector-store failure (→ 503) leaves file + registry intact (ADR-0020,
  no partial state); then removes `upload_dir/<document_id>` (tolerates a
  missing dir, e.g. registry-only rows); then registry entry; returns
  `DocumentDeleteResponse {document_id, deleted: true}`.
- `app/schemas/document.py`: new `DocumentDeleteResponse`.

Frontend:

- `lib/api.ts`: `deleteDocument(id)` → `DELETE /api/documents/{id}`
  (encodeURIComponent); non-2xx throws via existing `parse`.
- `types.ts`: `DocumentDeleteResult`.
- `components/DocumentsView.tsx`: per-row trash button (`Trash2` icon,
  variant ghost, aria-label `Delete <document_name>`, disabled + spinner
  while in flight); on success calls new `onDeleted(documentId)` prop and
  shows notice `<name> deleted.`; on failure shows `role="alert"` error panel
  and keeps the row.
- `App.tsx`: `handleDeleted` filters the document out of state (backend
  already confirmed the hard delete; no refetch).

Commits:

- `cf39de1` `feat(documents): hard-delete documents and add trash button to list`
  (7 files, +133/−5)
- (test fix during iteration, by test-writer decision of orchestrator:
  `d62cb33` `test(frontend): fix delete-call assertion to match recorded shape`)

Verification performed by implementer:

- `backend`: `uv run pytest -m "not integration"` — 126 passed, 3 skipped
  (after cleaning `backend/data`, see pre-existing-state note below); all
  4 new delete tests pass.
- `frontend`: `npx vitest run` — 27 passed (all 3 new delete tests pass).
- `uv run ruff check .` / `uv run mypy .` — clean (41 files).
- `npx tsc --noEmit` / `npx eslint` — clean; pre-commit hook green on both
  commits.

Pre-existing issue found (NOT caused by this task, out of scope):

- The existing upload tests (`tests/test_api_documents.py`,
  `tests/test_ingestion_robustness.py`) write to the REAL
  `backend/data/registry.json` + `backend/data/uploads` and never clean up,
  so a second consecutive full-suite run fails 4 upload tests with
  DUPLICATE results. Verified: after `rm -rf backend/data` the suite is
  126/126 green; rerunning immediately fails the same 4. Recommend a
  follow-up issue for test isolation (temp_upload_dir everywhere).

Note for verifiers: run the backend suite after `rm -rf backend/data` (or
accept the 4 known statefulness failures) until the follow-up lands.

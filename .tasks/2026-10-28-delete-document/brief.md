# Brief — Delete an uploaded document from the UI (file + data used for answers)

## [2026-10-28T09:52] orchestrator — brief v1 (draft, pending user confirmation)

### Objective

Let the user delete an uploaded document from the frontend: in the Documents
view, each row in the document list gets a trash-bin button. Clicking it deletes
that specific document everywhere it lives:

- the uploaded file (and its storage folder) from the filesystem,
- its entry in the document registry (`data/registry.json`),
- its chunks/embeddings from the Qdrant collection, so subsequent queries no
  longer retrieve or cite content from the deleted document.

### Problem (diagnosed by orchestrator, read-only)

- Backend has upload/list endpoints only (`backend/app/api/documents.py`); no
  delete endpoint exists.
- Files are stored at `data/uploads/<document_id>/<filename>`; metadata in
  `data/registry.json` (loaded/saved via `app/services/registry.py`).
- Chunks are upserted into the Qdrant collection `knowledge_base` with payload
  fields including `document_id` (`app/services/qdrant.py` has no
  delete-points-by-filter method yet — one is needed).
- Frontend `DocumentsView.tsx` renders the document list with upload/refresh
  only; `App.tsx` holds the documents state and a `load()` refresher; no delete
  affordance or API call exists (`frontend/src/lib/api.ts`).

### Scope

In:

- New backend endpoint `DELETE /api/documents/{document_id}` that hard-deletes
  the document from all three stores (filesystem, registry, Qdrant).
- `QdrantClient` gains a method to delete all points of a document
  (filter by payload `document_id`).
- Frontend: trash-bin button per row in the Documents list; click → call the
  API → remove the row / refresh the list; show feedback on success and an
  error notice if the delete fails; the row stays if deletion failed.
- Tests: backend pytest (endpoint contract + store cleanup), frontend vitest
  (button, API call, state refresh, error handling). TDD: fail first.

Out:

- No bulk delete, no soft-delete/tombstones, no undo.
- No changes to upload, query/RAG, enrichment, or facets behavior beyond the
  fact that deleted documents no longer contribute to answers.
- No authentication/authorization (single-user, per ADR-0004).
- No API-key/external-enrichment changes.

### Acceptance criteria (numbered, verifiable)

1. `DELETE /api/documents/{document_id}` for an existing document removes the
   uploaded file/folder from `settings.upload_dir`, removes the registry entry,
   and deletes all Qdrant points whose payload `document_id` matches, then
   returns success (2xx).
2. After deletion, `GET /api/documents` no longer lists the document, and a
   query that previously retrieved content from it no longer cites or uses it.
3. `DELETE /api/documents/{document_id}` for an unknown/nonexistent id returns
   404 and changes nothing.
4. The Documents view renders a trash-bin button on every document row; it is
   keyboard-accessible and labelled (accessible name) for screen readers.
5. Clicking the trash button on a row deletes that document (backend call),
   removes it from the list without a full page reload, and shows a success
   notice.
6. If the delete API call fails (non-2xx / network error), the UI shows an
   error notice and the document row remains in the list.
7. Backend tests (pytest) and frontend tests (vitest) encode the contract above
   and were written before the implementation (TDD); both suites pass
   afterwards, with `uv run ruff`, `uv run mypy`, `npx tsc --noEmit` and
   eslint clean.

### Constraints

- Stack rules from AGENTS.md §5/§6: Python + FastAPI + Pydantic, flat
  routers/services, no forbidden patterns (no repositories/DDD/CQRS/hexagonal).
- `uv` for backend tooling; npm/vite for frontend.
- Append-only `.tasks/`; conventional commits on the task branch only.
- Implementer never touches tests; test-writer never touches implementation.

### Affected area

- both (backend Python + frontend React)

### Component directories affected

- `backend/` (api, schemas, services/qdrant, tests)
- `frontend/` (components/DocumentsView, lib/api, types, tests)

### Involves UI changes?

- yes — Documents view (document list rows gain a delete/trash-bin button;
  success/error notices on delete)

### Stack URLs

- App served by backend at http://127.0.0.1:8000/ (compose `backend` service,
  same-origin `/api` proxy per ADR-0005)
- API base: http://127.0.0.1:8000/api (documents: GET/POST `/api/documents`,
  new DELETE `/api/documents/{document_id}`)
- E2E base URL (existing Playwright config): `E2E_BASE_URL` default
  http://127.0.0.1:8000

### Open questions (to resolve before confirmation)

1. Confirm-delete dialog: should clicking the trash button ask for confirmation
   (browser `confirm()` is acceptable) before deleting, or delete immediately?
2. Delete allowed for documents in any status (PROCESSING / FAILED / READY) or
   READY only? (Proposed: any status — users must be able to clean up failed
   uploads too.)
3. Success response contract: 200 with a JSON body
   (`{"document_id": ..., "deleted": true}`) vs 204 No Content. (Proposed: 200
   + JSON for consistency with the rest of the API.)
4. If Qdrant is unreachable during delete: fail the whole delete (error, keep
   everything) or proceed with file+registry removal anyway? (Proposed: fail —
   never leave chunks orphaned or a half-deleted document.)

### Decision capture (proposed ADR)

- Hard delete across all stores (filesystem + registry + Qdrant), no
  tombstones/undo — vs alternatives (soft-delete status flag, admin-only
  purge). To be drafted as ADR-0020 (Status: Proposed) via adr-writer if the
  user confirms the approach.

### Worktree

- /Users/menecio/code/wand-take-home-delete-document

### Branch

- feat/delete-document

### Base

- main (b107ef4)

## [2026-10-28T09:55] orchestrator — brief v1 confirmed by user (open questions resolved)

User answers to §Open questions:

1. No confirmation dialog — clicking the trash button deletes immediately.
2. Delete is allowed for documents in ANY status (PROCESSING / FAILED / READY).
3. Success response contract: 200 + JSON body `{"document_id": ..., "deleted": true}`.
4. If Qdrant is unreachable during delete: FAIL the whole delete, keep the
   document (no partial deletion, no orphaned chunks).
5. Deletion strategy: HARD delete across all stores — no soft-delete status,
   no tombstones, no undo. To be recorded as ADR-0020 (Status: Proposed;
   user confirms approach, human flips Status to Accepted).

These answers amend/refine the acceptance criteria as follows (superseding the
proposals in §Open questions):

- Criterion 4/5: the trash button deletes immediately, no confirm() step.
- Criterion 1: applies to every document status; DELETE of a document in any
  status succeeds the same way (file dir if present, registry entry, Qdrant
  points), returning 200 + `{"document_id": ..., "deleted": true}`.
- New criterion (deletion atomicity / no partial state): if any store removal
  fails (e.g. Qdrant unreachable), the DELETE returns an error (5xx/409) and
  the document remains fully intact in all stores.

Active acceptance criteria for this task = §Acceptance criteria 1–7 with the
refinements above.

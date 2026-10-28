# Report — visual-verifier, iteration 1 (verify-1)

## [2026-10-28T10:50] visual-verifier — verdict: PASS

Environment: branch stack brought up via compose override (scratchpad file,
NOT in the repo) — app on http://127.0.0.1:8001, branch-owned Qdrant on 6334,
branch Ollama container on 11435; the app reuses the already-running host
Ollama at 11434 for inference only. The user's main stack (ports 8000/6333/
11434) was not touched. Multi-stage image rebuilt from this branch.

Playwright runs (E2E_BASE_URL=http://127.0.0.1:8001):

- `e2e/delete-document.spec.ts` — upload via UI → `Delete <name>` button
  visible → click → row disappears, no alert — **1 passed**.
- `e2e/smoke.spec.ts` — root renders main heading — **1 passed** (no
  regression from the new table column).
- Live integration `tests/test_integration_document_delete.py` (Qdrant
  6334, host Ollama) — **1 passed**: deleted document not listed and not
  cited.

Visual evidence: screenshot of the Documents table showing the new Actions
column with a trash-bin icon button per row
(`scratchpad://documents-trash.png`, attached to the session).

Test defect found and fixed during verification (test-writer scope, no brief
amendment): the delete journey used `getByRole('link', { name: 'Documents' })`
which strict-mode-resolves to two links ("Documents" nav + "Go to Documents"
empty-state link); fixed with `exact: true`.

Pre-existing issue observed (out of scope, matches logic-verifier note):
`e2e/production-journey.spec.ts` uses the same ambiguous
`getByRole('link', { name: 'Documents' })` locator and would fail with the
same strict-mode violation on an empty KB — recommend including it in the
test-isolation/locator follow-up issue.

Verdict: PASS (UI criteria 4–6 verified end-to-end against the production
build).

# Implementation — iteration 1 (implementer)

## [2026-10-28T10:14] implementer — implemented per brief v1, tests untouched

### Changes

- `backend/app/config.py`: default `retrieval_threshold` 0.55 → **0.50** (AC-1).
  `RETRIEVAL_THRESHOLD` env override untouched (existing override test passes).
- `backend/app/services/query_pipeline.py` (AC-4):
  - `_insufficient_data_response()` now accepts optional `best_score` / `threshold`
    and appends a near-miss line to `missing_info`:
    `"Best retrieved relevance score 0.47 was below the 0.50 threshold."`
    (scores/threshold formatted with `:.2f`; both lines kept — original
    "No relevant evidence…" line preserved).
  - `generate_answer()` gate branch computes the best score over ALL retrieved
    chunks (`max(..., default=None)`) and passes it with
    `settings.retrieval_threshold`. With an empty result list (empty index) no
    near-miss line is added — nothing was retrieved to disclose.
- `backend/app/main.py` (AC-5): stdlib logging configuration at import time.
  Root logger `setLevel(INFO)` unconditionally (idempotent under test runners
  that already attach root handlers — avoids `basicConfig`'s no-op-with-handlers
  trap and avoids `force=True` which would detach the capture handler); a
  `StreamHandler` with formatter `%(levelname)s %(name)s %(message)s` is added
  only when the root logger has no handlers (plain uvicorn production case).
- `backend/app/api/documents.py` (AC-6): module logger; after a successful
  upsert `_process_uploaded_file` logs
  `"document processed: %s, %d chunks stored"` (name + chunk count).

### Verification (implementer-run, per hook contract)

- `uv run pytest -m 'not integration' -q`: **130 passed, 3 skipped** — all six
  TDD tests now pass; no pre-existing test broke.
- `uv run ruff check .`: clean. `uv run mypy app tests`: clean (40 files).
- One full-suite run initially showed 5 failures with status DUPLICATE vs
  READY — caused by leftover `backend/data/registry.json` from earlier TDD
  runs, NOT by the implementation. After `rm -rf backend/data` the suite is
  fully green (README already documents the clean-data-dir requirement).
- Observation for the orchestrator (no test edits allowed): the new
  document-processing test writes to the real `backend/data` registry instead
  of the conftest `data_dir` isolation fixture, so it inherits the suite-wide
  clean-data-dir requirement. Passing on a clean dir; no functional issue.

### Out of scope (untouched, per brief)

- Blocking Ollama/Qdrant calls in async endpoints (known, separate task).
- Frontend, API schema, generation prompt, dedup/budget logic.

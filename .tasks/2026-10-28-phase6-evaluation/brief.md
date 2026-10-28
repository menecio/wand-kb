# Brief — Phase 6: Evaluation and Critical Fixes

## [2026-10-28T00:00] orchestrator — brief v1

## Context

Phases 1–5 are complete and merged to `main` (HEAD `345a46e`). The system
implements the full CHALLENGE.md scope: multi-file upload (PDF/MD/TXT),
persistence, local Qdrant retrieval, local Ollama embeddings/generation,
structured answers (answer, confidence, is_complete, missing_info, citations,
facets), enrichment suggestions, gated irrelevant-query handling, and a React
frontend served same-origin by FastAPI at http://127.0.0.1:8000.

A separate pending task (`.tasks/2026-10-28-async-blocking-calls`, event-loop
blocking in query paths) is **frozen awaiting user confirmation** and is out of
scope for this phase; it is recorded as a known issue instead.

## Objective

Execute the Phase 6 evaluation set against the real integrated system, assess
retrieval/answer quality qualitatively, fix only critical defects, verify
persistence and same-origin UI behavior, record reproducible evidence, and
declare feature freeze.

## Acceptance Criteria

1. The evaluation set (15 required scenarios) is executed against the live
   stack, or each unexecuted case is marked BLOCKED with a concrete reason.
2. False acceptance and false rejection are reviewed together (threshold
   calibration only permitted after both are reviewed).
3. Answer support, citation validity, confidence, completeness, gaps, and
   suggestions are assessed qualitatively per live case.
4. Complete, partial, irrelevant, empty-index, duplicate, repeated-name,
   failed-ingestion, invalid-citation, and invalid-model-output paths have
   execution evidence (live or deterministic-test).
5. Document-based prompt injection does not override system instructions.
6. Persistence verified after `docker compose stop` + `up -d` (no `-v`).
7. Production same-origin build (`frontend/dist` served by FastAPI) exercised
   through the real UI.
8. Existing automated tests pass, or each failure is documented/classified.
9. Critical fixes are verified against the original defect and regressions.
10. README results/limitations reflect actual execution.
11. Evidence and executed commands stored under `.tasks/<this dir>/reports/`.
12. No optional features added; features declared frozen.

## Constraints

- Timebox 1.5 h; prioritize execution evidence over refinement.
- No docker compose down -v. No new features (no hybrid search, reranking,
  OCR, auto-enrichment, rating, streaming, new screens).
- Fixes must be minimal and evidence-driven; retrieval-threshold changes only
  after false-acceptance AND false-rejection review.
- Conventional Commits; work on a dedicated worktree/branch, never main.
- The pending `fix/async-blocking-calls` task is NOT executed (awaits user).

## Affected area

Backend (only if critical defects), docs (README, eval evidence), .tasks
evidence. No frontend feature work.

## Worktree / Branch

- Worktree: /Users/menecio/code/wand-take-home-phase6-eval (created in Phase 0)
- Branch: `chore/phase6-evaluation` (base main @ 345a46e)
- Base: main

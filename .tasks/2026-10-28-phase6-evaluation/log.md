
## [2026-10-28T02:45] orchestrator — Environment brought up; deterministic suites executed
- Stopped leftover phase-3 compose project (no volumes removed) to free port 8000.
- Seeded `wand-take-home-phase6-eval_ollama_data` from the phase-3 ollama volume
  (nomic-embed-text + qwen2.5:3b already present); no model re-download needed.
- Built `frontend/dist` (npm ci + npm run build); built app image; `docker compose -p wand-take-home-phase6-eval up -d`.
- Backend unit suite: 117 passed, 3 skipped (pre-fix). ruff + mypy: pass.
- Frontend: tsc --noEmit, eslint, vitest (16 tests): pass.
- README defect noted: documented eval command fails from repo root (no `requests`
  in root venv); corrected to run from `backend/`.

## [2026-10-28T02:50] orchestrator — Live evaluation executed
- `cd backend && uv run python ../eval/run_eval.py` — 14/14 cases against real
  Ollama + Qdrant (~3.6 min). Results: eval/RESULTS.md (archived copy in reports/).
- Live probes: empty index (INSUFFICIENT_DATA, structured gaps), duplicate upload
  (DUPLICATE, no overwrite), same filename different content (two docs coexist),
  corrupt PDF + valid file in one request (FAILED + READY, valid searchable),
  prompt-injection probe, two-document synthesis probe.

## [2026-10-28T03:05] orchestrator — Critical defect F-1 found, fixed, verified
- DEFECT: blank model answer accepted (`answer: ""` with a citation) on injection probe.
- TDD: test added first (red) — commit 4271f2a `test(backend): encode blank-answer rejection contract`.
- FIX: blank answer rejected in `_validate_and_assemble` → bounded retry → controlled
  error — commit 7368620 `fix(backend): reject blank model answers via bounded retry`.
- Verified: probe now returns INSUFFICIENT_DATA with zero citations; regression
  query still answered; backend suite 118 passed; ruff/mypy pass.

## [2026-10-28T03:15] orchestrator — Persistence, UI journeys, freeze
- Persistence: `docker compose stop` + `up -d` (no -v): 14 documents before == after; search works.
- E2E (production same-origin build): 4 passed — upload→query→citation open (excerpt
  verified against source), irrelevant query → INSUFFICIENT_DATA UI, refresh triggers
  only GET /api/documents, smoke test.
- Console/external audit: 0 console errors, 0 external requests.
- False-acceptance and false-rejection reviewed; threshold left at 0.55.
- Feature set FROZEN. Evidence: reports/evaluation-report.md, RESULTS-phase6-live.md,
  RESULTS-phase3-archived.md.

## [2026-10-28T03:25] orchestrator — Close: PR created
- PR: https://github.com/menecio/wand-take-home/pull/7 (chore/phase6-evaluation → main)
- All verdicts PASS (unit 118, lint/typecheck, vitest 16, e2e 4, live eval 14/14,
  persistence verified). Feature set frozen.
- Deliverable blocker noted: none. Pending user decision: async-blocking-calls task.

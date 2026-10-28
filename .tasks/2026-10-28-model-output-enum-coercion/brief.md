# Brief — Coerce near-miss enum values in model output instead of failing generation

## [2026-10-28T10:16] orchestrator — brief v1 (draft, pending user confirmation)

### Objective

When the generation model returns an enum value outside the allowed set (observed
live: `"confidence": "NONE"` from `qwen2.5:3b`), the pipeline must coerce it to
the semantically closest valid value and produce a proper structured response —
not discard the entire generation via the controlled-error path.

### Problem (observed live, 2026-10-28, user report + container logs)

- `POST /api/query` → model JSON `"confidence": "NONE"` →
  `_GenerationSchema` ValidationError (enum) → ValueError → bounded retry
  (attempt 2) → same `"NONE"` → `_ControlledAnswerError` →
  `_controlled_error_response("the model output could not be validated")`.
  User-visible result: "The system could not produce a verified answer: the
  model output could not be validated", confidence INSUFFICIENT_DATA, citations
  empty — a wasted generation for a recoverable output.
- The 0.50 gate (ADR 0020) admits more borderline context, so the model more
  often answers uncertain questions with `"NONE"` instead of the four allowed
  values. `"NONE"` semantically means "no confidence" → `INSUFFICIENT_DATA`.
- Enum matching is also case-strict: `"high"` / `"High"` would fail today, and
  the same brittleness exists for facet `status` (FacetStatus) and enrichment
  `action_type` (ActionType) inside `_GenerationSchema`.

### Scope

In:

- Pre-validation coercion of model-provided enum values in the generation
  schema (`backend/app/services/query_pipeline.py`, `_GenerationSchema`):
  - `confidence`: case-fold; aliases `NONE` / `UNKNOWN` / `UNSURE` / empty →
    `INSUFFICIENT_DATA` (no confidence ⇒ insufficient data; keeps IR-1..IR-6
    intact since INSUFFICIENT_DATA forces `is_complete=false`).
  - facet `status`: case-fold; unknown values (e.g. `UNKNOWN`, `NONE`) →
    `UNCERTAIN` (conservative: uncertainty is surfaced, never silently ANSWERED).
  - enrichment `action_type`: case-fold; unknown values → `ASK_USER`
    (most conservative suggestion).
- Valid values and all existing behavior unchanged; the bounded retry (ADR 0013)
  remains as the second chance for non-enum failures (blank answers, bad JSON).
- ADR 0021 (Status: Proposed) recording the coercion policy.

Out:

- No prompt changes, no model changes, no retry-count changes.
- No changes to `_validate_and_assemble`, IR invariants, citations assembly,
  conflict detection, retrieval/gating, or the API schema.
- No coercion of free-text fields (answer, missing_info, reasons) — only enums.
- Frontend untouched.

### Acceptance criteria (numbered, verifiable)

1. A generation attempt returning `"confidence": "NONE"` yields a normal
   structured response with `confidence=INSUFFICIENT_DATA`, `is_complete=false`,
   and the model's other fields preserved (answer text, facets, citations if
   valid) — NOT the generic controlled-error response.
2. Lowercase / mixed-case enum values (`"high"`, `"Answered"`) are accepted
   case-insensitively for confidence, facet status, and action_type.
3. Unknown facet `status` values (e.g. `"UNKNOWN"`) coerce to `UNCERTAIN`;
   unknown `action_type` values coerce to `ASK_USER`; the facet/suggestion is
   kept, not dropped.
4. Valid enum values (`HIGH`, `ANSWERED`, `UPLOAD_DOCUMENT`, …) pass through
   unchanged (no regression in existing validation tests).
5. The bounded retry still applies to non-enum failures (e.g. invalid JSON,
   blank answer) — unchanged behavior.
6. Full backend suite passes (`rm -rf backend/data && uv run pytest -m 'not
   integration'`), ruff + mypy clean; frontend suites unaffected.

### Constraints

- AGENTS.md §6: flat/simple; coercion lives in the generation schema only;
  stdlib/Pydantic only, no new dependencies.
- Tests only by test-writer (fail first); implementer never touches tests.
- Append-only `.tasks/` and ADR content; conventional commits on
  `fix/model-output-enum-coercion` only.

### Affected area / components

- Area: backend only (no UI changes → no visual-verifier phase).
- Component directories: `backend/` (app/services/query_pipeline.py —
  `_GenerationSchema` + helpers; backend/tests/). `docs/adr/0021-*.md`.

### Stack URLs

- App (UI + API, same origin): http://127.0.0.1:8000
- Backend API: http://127.0.0.1:8000/api
- Ollama: http://127.0.0.1:11434 · Qdrant: http://127.0.0.1:6333

### Pipeline metadata

- Worktree: /Users/menecio/code/wand-take-home-enum-coercion
- Branch: fix/model-output-enum-coercion
- Base: main (5b18eb1)
- ADR: 0021 (Status: Proposed)

### Open points for user confirmation

1. Alias policy as listed (NONE/UNKNOWN/UNSURE/empty → INSUFFICIENT_DATA;
   unknown facet status → UNCERTAIN; unknown action_type → ASK_USER) — OK?
2. Keep the bounded retry unchanged (no third attempt) — OK?

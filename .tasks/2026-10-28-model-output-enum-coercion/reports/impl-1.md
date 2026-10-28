# Implementation — iteration 1 (implementer)

## [2026-10-28T10:34] implementer — implemented per brief v1, tests untouched

### Changes

- `backend/app/services/query_pipeline.py` (single file, per brief):
  - `_CONFIDENCE_ALIASES = {"NONE", "UNKNOWN", "UNSURE", ""}` — values the model
    uses for "no confidence".
  - `_coerce_confidence`: case-folds (strip + upper); aliases →
    `INSUFFICIENT_DATA`. Unknown non-alias strings are case-folded and still
    fail validation (bounded retry / controlled-error path), per the confirmed
    brief.
  - `_coerce_facet_status`: case-fold; unknown values → `UNCERTAIN`
    (conservative — doubt surfaced, never silently ANSWERED; IR-2 untouched).
  - `_coerce_action_type`: case-fold; unknown values → `ASK_USER`.
  - `_coerce_facet_payload` / `_coerce_suggestion_payload`: copy the raw dict
    and coerce the enum field (no mutation of caller data).
  - `_GenerationSchema._coerce_model_enums`: `model_validator(mode="before")`
    normalizing the raw payload dict's `confidence`, each facet's `status`, and
    each suggestion's `action_type`. Applies only to the generation schema;
    public `Facet`/`EnrichmentSuggestion` models keep strict validation.
    Non-dict payloads pass through unchanged (pydantic handles them as before).
- Bounded retry unchanged (attempt loop untouched); no prompt/model changes.

### Verification (implementer-run)

- `rm -rf backend/data && uv run pytest -m 'not integration' -q`:
  **152 passed, 3 skipped** — all 18 coercion tests now pass, no pre-existing
  test broke.
- `uv run ruff check .` clean; `uv run mypy app tests` clean (41 files).

### Out of scope (untouched, per brief)

- Prompt wording, retry count, `_validate_and_assemble`, IR invariants,
  API schema, retrieval/gating, frontend.

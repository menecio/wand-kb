# Tests — iteration 1 (test-writer)

## [2026-10-28T10:26] test-writer — TDD tests for issue #15 (brief v1, criteria 1-5)

### Files

- `backend/tests/test_generation_coercion.py` (new, 22 tests):
  - `test_confidence_aliases_coerce_to_insufficient_data[NONE|UNKNOWN|UNSURE|""]` — AC-1.
  - `test_confidence_none_yields_structured_fields_not_error` — AC-1: coercion preserves answer/missing_info.
  - `test_confidence_is_case_insensitive[high|Medium|low|insufficient_data]` — AC-2.
  - `test_facet_status_unknown_coerces_to_uncertain[UNKNOWN|NONE|TBD]` — AC-3 (facet kept, not dropped).
  - `test_facet_status_is_case_insensitive` — AC-2 ("answered" accepted; IR-2 citation requirement still enforced via citation_ids present).
  - `test_action_type_unknown_coerces_to_ask_user[REQUEST_HUMAN|NONE|UPLOAD]` — AC-3 (suggestion kept).
  - `test_action_type_is_case_insensitive` — AC-2.
  - `test_valid_confidence_values_pass_through[HIGH|MEDIUM|LOW]` — AC-4 regression guard.
  - `test_valid_facet_and_action_values_pass_through` — AC-4 regression guard.
  - `test_none_confidence_generation_returns_structured_response` — AC-1 end-to-end: mocks `generate_structured` at the real seam (schema.model_validate_json of raw model JSON with `"confidence": "NONE"` and `"status": "UNKNOWN"` facet); asserts the model's own answer text and gap analysis survive (NOT the "could not produce a verified answer" controlled-error path), confidence INSUFFICIENT_DATA, facet coerced to UNCERTAIN.

### Design notes for implementer (constraints, not instructions)

- Coercion must live in `_GenerationSchema` only (public `Facet`/`EnrichmentSuggestion`
  models are shared with response validation and must stay strict) — e.g. a
  `model_validator(mode="before")` on `_GenerationSchema` normalizing the raw
  dict's `confidence`, each facet's `status`, and each suggestion's `action_type`.
- Per confirmed brief: unknown non-alias confidence strings are NOT coerced
  (still fail → bounded retry → controlled error). Only the specified aliases
  (NONE/UNKNOWN/UNSURE/empty) and case-folding are in scope.
- Valid enum values must pass through byte-identical (guards encode this).

### TDD status (pre-implementation)

- Full unit suite: **18 failed, 134 passed, 3 skipped** — all 18 coercion tests
  fail-first; the 4 regression guards pass by design; no pre-existing test broke.
- `uv run ruff check` + `uv run mypy` clean on the new file.
- One test-harness fix during authoring (model_validate → model_validate_json);
  noted for transparency, tests still fail-first as required.

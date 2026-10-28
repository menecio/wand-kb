# Tests — iteration 1 (test-writer)

## [2026-10-28T10:06] test-writer — TDD tests for issue #12 (brief v1, criteria 1-6, 8)

### Files

- `backend/tests/test_retrieval_gating.py` (appended; existing tests untouched except the new section placed before `test_gated_response_shape`):
  - `test_default_retrieval_threshold_is_0_50` — AC-1: default `retrieval_threshold` == 0.50, env override preserved by the existing `test_retrieval_settings_are_configurable` (still passes: it tests the override mechanism with 0.55).
  - `test_borderline_score_0_52_passes_gate_and_invokes_generation` — AC-2: 0.52 chunk (rejected at 0.55) reaches generation; asserts HIGH answer with citations and `generate_structured` called.
  - `test_irrelevant_band_score_0_46_still_gates_out_generation` — AC-3 guard: case_04 band stays gated, generation NOT invoked.
  - `test_gated_response_discloses_near_miss_score_and_threshold` — AC-4: gated `missing_info` contains a line with the best score ("0.47") and the threshold ("0.5…").
- `backend/tests/test_logging_observability.py` (new):
  - `test_app_import_enables_info_logging` — AC-5: subprocess imports `app.main` and asserts the root logger level is INFO (pre-fix root stays WARNING, which is exactly why `retrieval_gating` lines were invisible).
  - `test_retrieval_gating_log_is_emitted_without_forcing_levels` — AC-5: gated query emits the `retrieval_gating` JSON record (question, scores, threshold, `generation_invoked=false`) to root handlers WITHOUT `caplog.set_level` — fails pre-fix because INFO records are filtered out by the WARNING root logger.
  - `test_retrieval_gating_log_records_invoked_generation` — AC-5 contract guard: generation-invoked query logs `generation_invoked=true` (uses `caplog.set_level` for level stability; the content already exists in code).
  - `test_document_processing_emits_info_log_with_name_and_chunks` — AC-6: successful upload logs document name + stored chunk count; fails pre-fix (no such log line exists).

### TDD status (verified against current main, pre-implementation)

- `uv run pytest -m 'not integration' --tb=short -q` (from backend/): **6 failed, 124 passed, 3 skipped**.
- Failing (correctly, fail-first): threshold default, 0.52 passes gate, near-miss disclosure, root-INFO config, gating log emitted, processing log emitted.
- Passing by design (regression/contract guards for preserved behavior): 0.46 band still gated, generation-invoked log content.
- No pre-existing test broke. No existing test uses scores in the 0.50–0.55 band (scan: scores used are ≥0.8 or ≤0.15), so lowering the threshold cannot flip old expectations.

### Notes for implementer (constraints, not instructions)

- `eval/CALIBRATION.md` evidence append (AC-7) is docs work, no test.
- Lint/typecheck clean: `uv run ruff check` + `uv run mypy` pass on both files.

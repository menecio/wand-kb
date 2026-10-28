# Brief — Retrieval gate reliability + pipeline log visibility

## [2026-10-28T09:54] orchestrator — brief v1 (draft, pending user confirmation)

### Objective

Answerable questions must not be rejected by a razor-thin retrieval gate, and
gating/ingestion decisions must be observable in the application logs. Concretely:
recalibrate the deterministic retrieval gate (ADR 0012 mechanism kept) and make
the pipeline's existing structured logs actually visible.

### Problem (diagnosed by orchestrator on the live stack, read-only, 2026-10-28)

- Live measurements (nomic-embed-text + Qdrant cosine, current KB):
  - "how much was the approved budget?" scores **0.5710** vs the `meeting_notes.pdf`
    chunk — only 0.02 above the 0.55 gate.
  - Natural phrasings of the same question fall below the gate:
    "what is the approved budget?" → **0.5469** (gated, INSUFFICIENT_DATA in ~1s,
    generation never invoked), "approved budget" → 0.5214.
  - The vacation question scores 0.8369 (never borderline).
  - Irrelevant queries (eval case_04 band) score **0.44–0.46**.
- Embeddings were verified deterministic (fresh embedding of a stored chunk has
  cosine 1.0 with the stored vector; stable across Ollama model reloads; repeated
  queries give identical scores). This is a threshold-calibration problem, not an
  embedding-flakiness problem.
- The pipeline already emits a structured `retrieval_gating` INFO log (question,
  scores, threshold, `generation_invoked`) in `backend/app/services/query_pipeline.py`,
  but the app never configures logging, so the root logger stays at WARNING and the
  lines never appear in `docker compose logs app`. The gated `INSUFFICIENT_DATA`
  response also gives no hint of how close retrieval was.
- Upload processing is synchronous (extract → chunk → embed → Qdrant upsert
  `wait=true` → response), so "document not ready yet" is NOT the failure mode; but
  nothing in the logs shows that a document finished processing, which fed the
  user's confusion during diagnosis.

### Scope

In:

- Lower the default `retrieval_threshold` from 0.55 to **0.50** in
  `backend/app/config.py` (env override `RETRIEVAL_THRESHOLD` still respected).
- Near-miss disclosure: when the gate rejects (no chunk ≥ threshold), include the
  best retrieved score and the active threshold in `missing_info` of the
  `INSUFFICIENT_DATA` response (response schema unchanged: `missing_info` stays a
  list of strings).
- Logging visibility: configure application logging (stdlib only) so INFO records
  are emitted — the existing `retrieval_gating` JSON lines must appear in
  container logs for both gated and non-gated paths.
- Add one INFO log line on successful document processing (document name + number
  of chunks stored) in the upload path.
- Append recalibration evidence (2026-10-28 measurements above) to
  `eval/CALIBRATION.md` — append a new section, do not rewrite prior content.
- ADR 0020 (Status: Proposed) recording the recalibration + near-miss disclosure
  decision.

Out:

- No changes to the embedding model, chunking, deduplication, token budget,
  generation prompt, or Qdrant usage.
- No frontend/UI changes; no API schema changes (no new response fields).
- No hybrid search, reranking, or gap-based/dynamic gating (see ADR 0020
  alternatives).
- No threading/event-loop changes for the blocking Ollama/Qdrant calls
  (known issue, separate task if wanted).
- No changes to invariants IR-1…IR-6 or the validation/assembly logic.

### Acceptance criteria (numbered, verifiable)

1. Default `retrieval_threshold` is 0.50 in `backend/app/config.py`; the
   `RETRIEVAL_THRESHOLD` env override still works.
2. A query whose best retrieved chunk scores ≥ 0.50 (e.g. 0.52 — previously
   rejected at 0.55) invokes generation: a test spying on the generation client
   proves it is called and the response is a validated structured answer.
3. A query whose best retrieved chunk scores < 0.50 (e.g. 0.46, the case_04
   irrelevant band) does NOT invoke generation and returns `INSUFFICIENT_DATA`
   with `is_complete=false` and empty citations.
4. When the gate rejects, `missing_info` contains a line disclosing the best
   retrieved score and the active threshold (e.g. "Best retrieved relevance
   score 0.47 was below the 0.50 threshold"). Schema unchanged.
5. `retrieval_gating` INFO records (question, `retrieval_scores`, `threshold`,
   `generation_invoked`) are emitted on both gated and non-gated paths and are
   visible at INFO level (unit tests via caplog; logic-verifier also checks the
   line appears in `docker compose logs app` on the live stack).
6. Successful document processing emits an INFO line containing the document
   name and the number of chunks stored (unit test).
7. `eval/CALIBRATION.md` gains an appended recalibration section for 0.50 citing
   the 2026-10-28 evidence (answerable band 0.52–0.84 passes; irrelevant band
   0.44–0.46 still gated).
8. Full backend suite passes (tests encoding 0.55 are updated by test-writer),
   `uv run ruff` and `uv run mypy` pass.

### Constraints

- AGENTS.md §6: flat/simple backend (FastAPI + Pydantic), stdlib `logging` only,
  no new dependencies, no forbidden architecture patterns.
- Tests are written only by test-writer and must fail before implementation (TDD);
  implementer never touches tests.
- Append-only `.tasks/` and ADR content; conventional commits on the task branch
  only; no commits on `main`.
- Stack: uv for Python deps; runtime via Docker Compose; tests run on host.

### Affected area / components

- Area: **backend only** (no UI changes → no visual-verifier, no Playwright phase).
- Component directories: `backend/` (app/config.py, app/services/query_pipeline.py,
  app/api/documents.py or equivalent upload path, app/main.py for logging config,
  backend/tests/), plus `eval/CALIBRATION.md` (appended evidence) and
  `docs/adr/0020-*.md`.

### Stack URLs

- App (UI + API, same origin): http://127.0.0.1:8000
- Backend API base: http://127.0.0.1:8000/api
- Qdrant: http://127.0.0.1:6333 (host) / qdrant:6333 (compose network)
- Ollama: http://127.0.0.1:11434 (host) / ollama:11434 (compose network)

### Pipeline metadata

- Worktree: /Users/menecio/code/wand-take-home-retrieval-gating-logging
- Branch: fix/retrieval-gating-logging
- Base: main (b107ef4)
- ADR: 0020 (Status: Proposed) — docs/adr/0020-lower-retrieval-threshold-050-near-miss-disclosure.md

### Open points for user confirmation

1. Threshold value: **0.50** recommended (evidence-based). Alternative: keep 0.55
   and only fix logging — but then the reported false-rejection class stays.
2. Near-miss disclosure in `missing_info` (criterion 4) — in or out?
3. Document-processing INFO log (criterion 6) — in or out?

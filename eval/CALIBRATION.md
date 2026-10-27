# Phase 3 Retrieval Threshold Calibration

## Chosen threshold

`RETRIEVAL_THRESHOLD = 0.55` (cosine similarity)

## Justification

The threshold was chosen by running the Phase 3 evaluation cases against the
live stack (Ollama `nomic-embed-text` + Qdrant cosine distance) and inspecting
the retrieved scores. The goal is to:

1. Accept enough context to answer the answerable cases.
2. Reject irrelevant or tangential fragments that would otherwise mislead the
   generative model.

Observations from the evaluation run recorded in `eval/RESULTS.md`:

- Answerable facts (vacation days, product price, project deadline, RTO,
  responsibility assignments) retrieved chunks with scores in the 0.60–0.84
  range, well above 0.55.
- The deliberately irrelevant query (case_04: "What is the competitor's pricing
  strategy?") returned fragments with scores 0.44–0.46, below the threshold, so
  the pipeline correctly gated out without invoking generation.
- The ambiguous/conflict-aware cases (case_03, case_11) retrieved borderline
  fragments around 0.55. Raising the threshold much higher would risk false
  rejections of genuinely answerable questions; lowering it would let more
  tangential fragments through.

## Observed false rejections

- **case_08 — "Are there any conflicts in the documents?"** (expected: complete)
  The query is global/meta in nature and does not match any single chunk
  strongly. All retrieved scores fell below 0.55, so the system returned
  `INSUFFICIENT_DATA` instead of answering. This is a known limitation of dense
  retrieval without aggregation or a dedicated conflict-detection pass.

## Observed false acceptances / near-misses

- **case_03 — "What are the company policies and what products do we sell?"**
  (expected: complete) Retrieved fragments scored 0.55–0.64 and passed the gate,
  but the model produced a `LOW` confidence, incomplete answer. The fragments
  were thematically related but did not contain enough product information to
  fully answer the question. This suggests the threshold is at the edge of
  usefulness for broad synthesis questions.

- **case_11 — "What is the recovery time objective for Acme production
  systems?"** (expected: insufficient/conflict) The two contradiction documents
  retrieved high-scoring fragments (0.76 and 0.73), which is correct, but the
  model reported `is_complete=True` and `confidence=HIGH` rather than flagging
  the conflict. The retrieval step did its job; the completeness/conflict
  classification remains sensitive to model behavior.

## Tuning notes

- `RETRIEVAL_TOP_K = 5` keeps the context small and focused. Increasing it did
  not appear necessary for the evaluated cases.
- `MAX_CONTEXT_TOKENS = 2048` limits the prompt to roughly the top 5 chunks for
  `nomic-embed-text` chunk sizes, avoiding context bloat.
- The threshold is intentionally conservative. A higher value (e.g., 0.60) would
  likely gate out case_03 entirely but might also reject valid partial answers;
  a lower value (e.g., 0.50) would let in more noise from case_04-like queries.

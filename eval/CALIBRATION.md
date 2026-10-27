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

Observations from the evaluation runs recorded in `eval/RESULTS.md`:

- Answerable facts (vacation days, product price, project deadline, RTO,
  responsibility assignments) retrieved chunks with scores in the 0.60–0.84
  range, well above 0.55.
- The deliberately irrelevant query (case_04: "What is the competitor's pricing
  strategy?") returned fragments with scores 0.44–0.46, below the threshold, so
  the pipeline correctly gated out without invoking generation.
- The ambiguous/conflict-aware cases (case_03, case_11, case_14) retrieved
  borderline or high-scoring fragments around 0.55–0.89. Raising the threshold
  much higher would risk false rejections of genuinely answerable questions;
  lowering it would let more tangential fragments through.

## Observed false rejections

- **case_08 — "Are there any conflicts in the documents?"** (expected: complete)
  The query is global/meta in nature and does not match any single chunk
  strongly. All retrieved scores fell below 0.55, so the system returned
  `INSUFFICIENT_DATA` instead of answering. This is a known limitation of dense
  retrieval without aggregation or a dedicated conflict-detection pass.

## Observed false acceptances / near-misses

- **case_03 — "What are the company policies and what products do we sell?"**
  (expected: complete) Retrieved fragments scored 0.55–0.64 and passed the gate,
  but the model produced an incomplete answer. The fragments were thematically
  related but did not contain enough product information to fully answer the
  broad synthesis question.

## Known defects / evaluation deltas (post Amendment 1 / ADR 0016)

The following cases deviated from their expected outcome in the most recent
live run recorded in `eval/RESULTS.md`. All other cases (case_02, case_04,
case_05, case_07, case_09, case_12, case_13) matched their expected behavior.

- **case_01 — "How many vacation days do employees get?"** (expected: complete)
  Returned `confidence=MEDIUM`, `is_complete=False`, with an enrichment
  suggestion noting that "the policy document is incomplete as it contains
  multiple versions of the policy with varying vacation days." The retrieval
  step returned the canonical `company_policy.md` vacation chunk (20 days) along
  with the coexisting `same_name_v1.md` (ten days) and `same_name_v2.md` (twenty
  days) chunks. The model treated this as a material conflict rather than a
  single confident answer.

- **case_03 — "What are the company policies and what products do we sell?"**
  (expected: complete) Returned `confidence=MEDIUM`, `is_complete=False`. The
  retrieved fragments were policy-oriented and did not contain product
  information, so the model correctly identified a missing facet.

- **case_06 — "What is the model number for the device with 12-hour battery?"**
  (expected: complete) Returned `confidence=LOW`, `is_complete=False`. The
  product spec chunk passed the gate but does not actually contain a model
  number; generation succeeded and correctly reported the missing facet.

- **case_08 — "Are there any conflicts in the documents?"** (expected: complete)
  Returned `confidence=INSUFFICIENT_DATA`, `is_complete=False`, generation not
  invoked. Dense retrieval did not return any fragment above threshold for this
  meta/global question.

- **case_10 — "What are the product specifications and who approved the
  budget?"** (expected: complete) Returned `confidence=MEDIUM`,
  `is_complete=False`. The budget approver is not explicitly named in the
  meeting notes, so the model correctly marked the budget-approval facet as
  partially answered.

- **case_11 — "What is the recovery time objective for Acme production
  systems?"** (expected: insufficient/conflict) Returned `confidence=HIGH`,
  `is_complete=True`. The retrieval step returned both contradictory chunks
  (`contradiction_a.md`: 1 hour; `contradiction_b.md`: 4 hours), but the model
  cited only the 1-hour sources. The backend conflict detector is conservative
  (it inspects only the citations the model provides for a facet), so the
  conflict was not downgraded automatically. This remains a model-dependent
  limitation.

- **case_14 — "How many vacation days do employees receive?"** (expected:
  insufficient/conflict) Returned `confidence=HIGH`, `is_complete=True`. The
  retrieval step returned the canonical vacation chunk (20 days) together with
  `same_name_v1.md` (ten days) and `same_name_v2.md` (twenty days), but the
  model cited only the canonical 20-day chunk. The conservative same-facet
  citation check therefore did not detect the conflict.

## Integration-test flakiness

The live integration suite is non-deterministic because `qwen2.5:3b` sometimes
classifies an obviously answerable question as incomplete on the first run and
complete on a retry. This has been observed for `test_integration_complete_answer`
("How many vacation days do employees get?"). The backend derivation correctly
forces `is_complete=False` whenever the model reports any non-ANSWERED facet,
but the model's facet classification itself varies across runs. This is
recorded as a known model-quality limitation.

## Tuning notes

- `RETRIEVAL_TOP_K = 5` keeps the context small and focused. Increasing it did
  not appear necessary for the evaluated cases.
- `MAX_CONTEXT_TOKENS = 2048` limits the prompt to roughly the top 5 chunks for
  `nomic-embed-text` chunk sizes, avoiding context bloat.
- The threshold is intentionally conservative. A higher value (e.g., 0.60) would
  likely gate out case_03 entirely but might also reject valid partial answers;
  a lower value (e.g., 0.50) would let in more noise from case_04-like queries.
- The backend conflict-detection heuristic (ADR 0016) is deterministic for the
  numeric-contradiction class *when the model cites conflicting sources for the
  same facet*. Non-numeric conflicts, subtle paraphrases (e.g., "1 hour" vs
  "60 minutes"), and conflicts the model excludes from its citations remain
  model-dependent.

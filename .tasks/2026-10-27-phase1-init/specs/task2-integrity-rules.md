# Data Contract Integrity Rules

These invariants MUST hold across all pipeline phases. They are non-negotiable constraints on the RAG system's behavior.

## QueryResponse Invariants

### IR-1: Factual Answers Require Valid Citations
Every factual claim in `answer` MUST be supported by at least one `Citation` in the `citations` list. An answer without citations is only acceptable when `confidence == INSUFFICIENT_DATA` and `is_complete == false`.

### IR-2: Answered Facets Require Evidence
For each facet with `status == ANSWERED`, there MUST be at least one corresponding `Citation` where `chunk_id` appears in the facet's `citation_ids` list.

### IR-3: Completeness Implies No Material Gaps
When `is_complete == true`, the `missing_info` list MUST be empty AND there MUST be no facets with `status` in `[MISSING, UNCERTAIN, CONFLICTING]`.

### IR-4: INSUFFICIENT_DATA Implies Incomplete
When `confidence == INSUFFICIENT_DATA`, then `is_complete` MUST be `false`. The system cannot claim completeness when data is insufficient.

### IR-5: No External References
All `Citation.document_id` values MUST correspond to documents that exist in the system. Citations cannot reference documents outside the retrieved context.

### IR-6: Suggestions Correspond to Gaps
Every `EnrichmentSuggestion` in `enrichment_suggestions` MUST correspond to at least one identified gap (a facet with `status` in `[MISSING, PARTIAL, UNCERTAIN, CONFLICTING]`). The `reason` field MUST explicitly reference the gap.

## Validation Rules

### Citation Relevance
- `relevance_score` MUST be in range [0.0, 1.0]
- Higher scores indicate stronger relevance to the query

### Document Status Transitions
Valid transitions for `DocumentSummary.status`:
- `PROCESSING → READY` (successful ingestion)
- `PROCESSING → FAILED` (ingestion error)
- No transitions from `READY` or `FAILED`

### Facet Status Semantics
- `ANSWERED`: Question fully answered with high confidence
- `PARTIAL`: Partial answer available, some gaps remain
- `MISSING`: No relevant information found
- `UNCERTAIN`: Information found but confidence is low
- `CONFLICTING`: Multiple sources provide contradictory information

## Enforcement

These rules are enforced through:
1. Pydantic model validation (type constraints, field constraints)
2. Business logic validation in the RAG pipeline
3. Test coverage verifying each invariant

Violations of these invariants indicate a bug in the pipeline implementation.

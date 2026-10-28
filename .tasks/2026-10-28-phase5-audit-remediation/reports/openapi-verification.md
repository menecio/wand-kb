# TS ↔ OpenAPI verification (work item 11, DoD)

Date: 2026-10-28. Source: live `/openapi.json` from the running FastAPI app
(phase5-audit worktree build, generated from `backend/app` schemas).

## Method

Fetched `http://127.0.0.1:8001/openapi.json` and compared, field by field,
every schema the frontend consumes in `frontend/src/types.ts`.

## Results

| OpenAPI schema | types.ts type | Verdict |
|---|---|---|
| DocumentStatus (enum: PROCESSING, READY, FAILED, REJECTED, DUPLICATE) | `DocumentStatus` | match |
| DocumentSummary (document_id, document_name, content_sha256, status, error?, created_at) | `DocumentSummary` | match |
| DocumentList | `DocumentList` | match |
| UploadResultItem (filename, status, document_id?, error?) | `UploadResultItem` | match |
| DocumentUploadResult | `DocumentUploadResult` | match |
| ConfidenceLevel (HIGH, MEDIUM, LOW, INSUFFICIENT_DATA) | `Confidence` | match |
| ActionType (UPLOAD_DOCUMENT, QUERY_EXTERNAL_SYSTEM, ASK_USER) | `ActionType` | match |
| Citation (chunk_id, document_id, document_name, page_start?, page_end?, section?, excerpt, relevance_score) | `Citation` | match (nullability identical) |
| EnrichmentSuggestion (action_type, target, reason, suggested_query?) | `EnrichmentSuggestion` | match |
| QueryRequest (question) | `QueryRequest` | match |
| QueryResponse (response_id, answer, confidence, is_complete, missing_info, enrichment_suggestions, citations, facets?) | `QueryResponse` | see note |

## Divergence note (single)

`QueryResponse.facets` (optional `Facet[]`: description, status, citation_ids,
associated_gap) is **not represented** in `types.ts`. This is intentional and
conformant: facets are internal diagnostics that the Phase 5 spec forbids
displaying (§2 out-of-scope "facet-level dashboard", §4 forbidden fabrication
"non-public facets"). TypeScript interfaces may omit optional fields the client
ignores; there is no unverified duplication.

## Contract observations surfaced (not changed by this task)

1. **Backend error strings can leak internal paths.** The FAILED row for a
   corrupt PDF returned: `Failed to open file '/Users/.../uploads/<id>/broken.pdf'
   as type pdf.` The UI spec (§3) forbids internal paths, but §4/§8 require
   displaying backend-returned errors verbatim and §12 forbids silently
   repairing contract inconsistencies in the browser. Recorded as **ADR 0018
   (Proposed)**: sanitize at the backend (minimal change), never in the UI.
2. `UploadResultItem.document_id` is `null` only for `REJECTED` uploads
   (verified in `backend/app/api/documents.py`); `DUPLICATE` reuses the
   existing document's id. The frontend handles both without fabricating
   identities (rejected files are reported in the notice only).

## Verdict

**No drift.** `frontend/src/types.ts` is verified against the live OpenAPI
contract; the single optional omission (`facets`) is documented and in scope
per the Phase 5 spec.

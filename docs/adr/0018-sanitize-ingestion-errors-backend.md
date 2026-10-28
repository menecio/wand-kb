# 0018. Sanitize ingestion error messages at the backend

- Status: Proposed
- Date: 2026-10-28
- Context: During Phase 5 audit verification, a corrupt PDF upload produced the backend error string `Failed to open file '/Users/.../uploads/<uuid>/broken.pdf' as type pdf.` The Phase 5 UI spec §3 requires the UI never to show stack traces or internal paths, while §4/§8 require displayed errors to be those returned by the backend, and §12 forbids silently repairing contract inconsistencies in the browser. The frontend cannot satisfy both rules for this input; the conflict originates in the backend's raw exception text.
- Decision: (proposed) Return sanitized, user-safe error messages from the ingestion pipeline at the backend (e.g. `The PDF file could not be opened or parsed.`), keeping detailed diagnostics in server logs. The frontend continues to render `error` verbatim. No change made in this task: this ADR documents the verified mismatch and the smallest proposed adjustment, per the brief's contract-change rule.
- Alternatives considered:
  - Frontend string-filtering of error text — rejected: silently rewrites contract data and hides defects (§12).
  - Truncation in the UI — rejected: loses the per-file safe error the spec requires (§17 "Upload failed: show the safe error for the specific file").
  - No action — rejected: leaves an internal-path disclosure on a user-facing surface.
- Consequences: One small backend change (out of the current frontend-only scope) closes the mismatch; until then the UI shows the backend error verbatim, including the path, as a visible contract defect rather than a concealed one.

# Brief: Phase 5 Frontend Completion (Audit Remediation)

- **Task dir:** `.tasks/2026-10-28-phase5-audit-remediation/`
- **Worktree:** `/Users/menecio/code/wand-take-home-phase5-audit`
- **Branch:** `fix/phase5-frontend-audit`
- **Base:** `main` @ `345a46e`
- **Affected area:** frontend only (`frontend/`); no backend edits expected
- **UI flag:** yes (Playwright config already exists)
- **Stack URLs:** `http://127.0.0.1:8000` (same-origin FastAPI + `frontend/dist`); dev proxy `/api/*` → `127.0.0.1:8000`
- **Brief provenance:** supplied directly by the user on 2026-10-28; recorded verbatim below and confirmed by that act.

## Objective
Close the gap between the implemented frontend and the Phase 5 React Frontend
Brief & UI/UX Specification (Section markers referenced from
`Phase_5_Frontend_and_UX_Brief.pdf`): deliver the sober dark visual language,
responsive behavior, and the specific behavioral corrections found in the
2026-10-28 frontend audit, without extending scope beyond the brief.

## Context / Source of truth
- Spec: `/Users/menecio/Downloads/Phase_5_Frontend_and_UX_Brief.pdf` (§7 Screens,
  §8/§10 Elements, §12 Result composition, §13 Screen-state matrix, §14 Responsive,
  §15 Design tokens, §16 Responsive/Motion/Components, §17 Accessibility/Content)
- Audit findings are the task list; do not re-litigate compliant items
  (contracts, API usage, state ownership, journey logic are already conformant).
- Backend is authoritative; no contract changes unless a verified mismatch is found,
  in which case document it as a Proposed ADR first.

## Scope
Affected area: **frontend only** (`frontend/`) + no backend edits expected.
UI flag: yes. Playwright config already exists.

## Work items (from audit)

1. **Design token system** (§15): implement the full OKLCH token set in
   `frontend/src/index.css` as CSS variables (`--surface-page`, `--surface-panel`,
   `--surface-raised`, `--stroke-default`, `--text-primary`, `--text-secondary`,
   `--state-active`, `--state-success`, `--state-warning`, `--state-danger`),
   Be Vietnam Pro (400/500/600) + IBM Plex Mono (400/500/600) typography,
   spacing scale 4–48px, topbar 68px, content max-width 1180px, primary controls
   min-height 42px, action border-radius 3px, 1px border panels, no shadows/
   gradients/decorative elements, visible focus (2px outline, 3px offset,
   state-active color). Dark theme only; no alternate light theme.
2. **App shell** (§7, §16): two-view shell with proper topbar + horizontal
   navigation styling, merge with existing `aria-current` nav; sidebar becomes
   horizontal navigation at ≤820px; main padding rules per spec.
3. **shadcn Button and Textarea** (§10, §17): replace the raw native button and
   textarea in `QueryView`/`DocumentsView`; the rest of the components may stay local.
4. **Spinner + reduced motion** (§16): text + spinner for uploads and query
   pending states; `prefers-reduced-motion` respected; spinner never the only indicator.
5. **DocumentsView corrections**: 
   a. Separate `loading` state — generic wait, never show "No sources yet."
      while the initial GET is pending.
   b. Empty state explains that no sources exist and prioritizes the upload action.
   c. Upload notice must reflect the actual ingestion result (files ready, files
      failed, duplicate/existing-document notice if the contract provides it) —
      not a blanket "Upload complete."
   d. Reconcile uploaded rows against the existing list by `document_id`
      (update existing, append new) instead of blind append.
   e. Audit the `upload-${item.filename}` fallback for null `document_id`;
      replace with a non-colliding safe representation without inventing identity.
6. **QueryView corrections**:
   a. Empty-index state includes a navigation link to Documents (J5).
   b. Block or clearly associate question editing with the in-flight request
      (spec allows either; pick one).
7. **CitationList corrections** (§12): heading shows source count;
   first citation open by default; C1/C2 presentational labels derived from
   order (chunk_id remains the real identity).
8. **StatusBadge**: add complementary icons (16–19px lucide or equivalent,
   aria-hidden) to text labels; state must remain readable without color.
9. **Responsive behavior** (§14, §16): two-column answer/evidence >900px, one
   column ≤900px, full-width actions and stacked header ≤560px, no horizontal
   overflow at 320–390px, long names ellipsis/wrap, document errors below the
   row on mobile, empty error cells leave no placeholder rows.
10. **Accessibility rehearsal** (§17/§18 DoD): labels on inputs, keyboard-
    operable dismiss/citations, aria-current/aria-expanded/role=status already
    present — verify focus order, touch targets near 42–44px, contrast on real
    backgrounds.
11. **TS/OpenAPI check** (DoD): verify `frontend/src/types.ts` against live
    `/openapi.json`; note any drift; generate or record explicit verification.

## Acceptance Criteria
1. Production build (`npm run build`) renders the dark token-based UI at
   127.0.0.1:8000 served by FastAPI; no light theme, no shadows/gradients.
2. Desktop 1440px: two-column answer+evidence; Documents table uses full width;
   hierarchy question → answer → gaps → suggestions → evidence.
3. Mobile 390px and 320px: no horizontal overflow; one-column results;
   evidence expandable after the answer; document error visible below failed row.
4. Query empty-index state shows the recommended microcopy AND a working link
   to Documents.
5. Initial Documents load shows a generic wait; the definitive empty message
   appears only after a successful empty GET response.
6. Upload notice reflects per-file outcomes including failures and
   duplicate/idempotent results from the real contract; no fabricated
   "new document" claims.
7. Uploaded rows reconcile with `GET /api/documents` data by `document_id`;
   no duplicate rows for already-present documents.
8. Citations: Evidence heading includes source count, first item open by
   default, C1/C2 labels present, remaining items toggle with aria-expanded.
9. StatusBadge pairs readable text with aria-hidden icon for all statuses
   rendered from the contract.
10. Pending query state shows text + spinner; respects prefers-reduced-motion;
    editing during a pending request is either blocked or unambiguously part of
    the in-flight request.
11. Keyboard: all controls reachable and operable; visible focus per tokens;
    touch targets ≥ ~42px on primary actions; no color-only states.
12. No scope creep: no rating, health widgets, metrics, doc inspector,
    streaming, OCR, auto-enrichment, extra screens, or demo data.
13. Existing unit tests (vitest) and e2e smoke test pass; new tests cover at
    least AC-4, AC-5, AC-8; lint/typecheck pass.

## Constraints
- Timebox: remainder of the Phase 5 budget (~2h suggested); cut order per spec
  §18 priority: animation/aesthetics first, never error states or citations.
- No backend, docker, or contract changes unless a genuine mismatch is proven.
- Keep components local and simple; no new state layer; no repository/abstraction
  patterns (see repo architecture rules).
- Mocking only in vitest/jsdom and Playwright network stubs, never in the running app.
- Preserve append-only `.tasks/` evidence: log decisions, screenshots (desktop +
  390px after production build), and any ADR references.

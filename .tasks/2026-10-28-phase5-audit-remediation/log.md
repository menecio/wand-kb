# Log — Phase 5 Frontend Completion (Audit Remediation)

## [2026-10-28T11:05] orchestrator — Phase 0: worktree, branch, brief recorded

- Worktree: `/Users/menecio/code/wand-take-home-phase5-audit` created from `main` @ `345a46e`.
- Branch: `fix/phase5-frontend-audit` (branch recorded in `brief.md`).
- Brief: supplied directly by the user (2026-10-28 frontend audit remediation, 11 work items, AC-1..AC-13); recorded verbatim in `brief.md` and treated as confirmed by that act.
- Spec re-read in full from `Phase_5_Frontend_and_UX_Brief.pdf` (§7–§18).
- Existing frontend reviewed: `App.tsx`, `DocumentsView.tsx`, `QueryView.tsx`, `AnswerResult.tsx`, `CitationList.tsx`, `StatusBadge.tsx`, `EnrichmentSuggestions.tsx`, `lib/api.ts`, `types.ts`, `App.test.tsx`, `e2e/smoke.spec.ts`. Audit's "already conformant" claims (contracts, API usage, state ownership, journey logic) confirmed against code.
- Backend ingestion semantics verified in `backend/app/api/documents.py` + `backend/app/schemas/document.py`: `REJECTED` → `document_id: null` (no registry row); `DUPLICATE` → reuses the existing READY document's id (no registry row added); `READY`/`FAILED` → new uuid with a registry row. This grounds work items 5c/5d/5e.

## [2026-10-28T11:10] orchestrator — design decisions (Proposed ADRs + interpretation)

- **ADR 0017 (Proposed)**: shadcn-style local `Button`/`Textarea` mirroring the shadcn component contract, styled with §15 tokens in `index.css`; full Tailwind/Radix adoption rejected for scope/YAGNI. Supersedes part of ADR 0010 (still Proposed).
- **Item 5e resolution**: `document_id: null` occurs only for `REJECTED` uploads (verified in backend). Rejected files get no fabricated row/identity; they are reported per-file in the upload notice (`role=status`). The `upload-${item.filename}` fabricated fallback is removed entirely.
- **Item 5d resolution**: uploaded rows reconcile against the current list by `document_id` (update existing in place, append new). No fabricated `content_sha256`/`created_at` are invented for appended rows — the summary fields the table renders (name, status, error) come from the upload response.
- **Item 6b resolution (spec §10 allows either)**: question editing is *blocked* while the request is in flight (`disabled` textarea), removing ambiguity.
- **Item 3 resolution**: `Button` used for all action buttons (Run query, Retry, New query, Upload documents, dismiss); `Textarea` for the question; the file input remains a visible, labeled native control (accessibility beats hiding it; audit item only demands Button/Textarea replacement).
- Typography via self-hosted `@fontsource/be-vietnam-pro` + `@fontsource/ibm-plex-mono` (400/500/600) — no external font CDN, matching the no-external-calls rule. Icons via `lucide-react` (16–19px, `aria-hidden`), per §15/§8.

## [2026-10-28T11:40] test-writer — audit tests written (red)

- `frontend/src/App.audit.test.tsx` added: 8 tests covering AC-4, AC-5, AC-6 (mixed + duplicate notice), AC-7, AC-9, AC-10, AC-8. All failed against the pre-remediation implementation (verified before coding). Commit `f691370`.

## [2026-10-28T11:55] implementer — remediation implemented (green)

- Commit `8173d9f`: OKLCH token system in `index.css` (§15), self-hosted Be Vietnam Pro + IBM Plex Mono (400/500/600) via @fontsource, 68px topbar shell + horizontal nav, local shadcn-style Button/Textarea (ADR 0017), Spinner + reduced-motion CSS, StatusBadge icons (lucide, aria-hidden), Documents loading/empty/per-file-notice states, document_id reconciliation (no fabricated ids for rejected uploads), QueryView empty-index link + blocked editing while pending, CitationList count + C1/C2 + first-open, responsive grid (2 cols >900px) and mobile table (errors below row, empty cells removed).
- New runtime deps: `lucide-react`, `@fontsource/be-vietnam-pro`, `@fontsource/ibm-plex-mono` (self-hosted; no external font CDN, no AI calls from the browser).

## [2026-10-28T12:00] orchestrator — Amendment 1 (test-selector alignment)

- Implementer reported collisions between mandated behaviors (AC-4 link, AC-8 first-open, J1 "Running") and loose matchers in the pre-existing suite. Amendment 1 appended to `brief.md`; selectors narrowed, deferred fetch mocks wrapped in `jsonResponse` (two mock bugs in the new tests were also found and fixed). Commit `6f52a94`. No acceptance criteria changed.

## [2026-10-28T12:45] logic-verifier — verify-1 verdict: PASS

- 24/24 vitest, eslint 0 problems, tsc clean, `npm run build` succeeds, e2e smoke passes against the production same-origin build. Full report: `reports/logic-verification.md`.
- Item 11 verified against live `/openapi.json`: no drift in any consumed schema; optional `facets` intentionally unrepresented (internal, §2/§4). Report: `reports/openapi-verification.md`.
- Contract observation: backend ingestion errors can leak internal paths → **ADR 0018 (Proposed)** filed; frontend deliberately left verbatim per §4/§12.

## [2026-10-28T12:45] visual-verifier — verify-1 verdict: PASS

- 19/19 scripted live checks pass against the production build served by FastAPI (worktree app on 127.0.0.1:8001; the running phase6-eval stack on 8000 was not touched). Screenshots: desktop 1440 (ask + documents), 390 (ask, evidence-open, documents), 320 (documents). Full results + WCAG AA contrast table: `reports/visual-verification.md`.
- Found and fixed during the run: horizontal overflow at 320–390px from unbreakable error strings (`overflow-wrap: anywhere` added to error cells; rebuilt and re-verified 0px delta at both widths).
- AC-12 scope check: no rating, health widgets, metrics, inspector, streaming, OCR, auto-enrichment, extra screens, or demo data added.

## [2026-10-28T12:50] orchestrator — status

- All verdicts PASS on verify-1 (no second round needed). Evidence complete: brief (with Amendment 1), this log, ADRs 0017/0018 (both Proposed, awaiting user decision), reports (logic, openapi, visual), screenshots.
- Awaiting user decision on: ADR 0017/0018 status, and integration (PR from `fix/phase5-frontend-audit` or ff-only rebase into `main` per AGENTS.md §7).

## [2026-10-28T13:05] orchestrator — pr-creator: PR opened; phase closed

- Branch `fix/phase5-frontend-audit` pushed to origin (7 commits).
- PR opened to `main`: https://github.com/menecio/wand-take-home/pull/9 (links issue #8 via `Closes #8` and the evidence under `.tasks/2026-10-28-phase5-audit-remediation/`).
- All verdicts PASS (verify-1, single round; no CHANGES, no repeats, no escalation).
- Outstanding user decisions recorded in the PR: ADR 0017 and ADR 0018 remain Proposed. Worktree cleanup deferred until the user confirms merge (AGENTS.md §7).

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

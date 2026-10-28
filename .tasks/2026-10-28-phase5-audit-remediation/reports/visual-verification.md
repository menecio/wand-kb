PASS keyboard focus order reaches nav + composer — Knowledge base | Ask & answers | Documents | TEXTAREA | 
    Knowledge baseAsk & answersDocumentsAsk & answersQuestionRun query
  


PASS documents table lists seeded rows — rows=6
PASS failed row shows its backend error
PASS upload notice reports idempotent duplicate — 1 already uploaded: handbook.pdf — no new document was created.
PASS no duplicate row appended for already-present document — before=3 after=3
PASS no horizontal overflow at 390px (documents) — delta=0px
PASS no horizontal overflow at 320px — delta=0px
PASS submit shows Running while pending
PASS pending wait indicator removed after answer
PASS no horizontal overflow at 390px (ask) — delta=0px
PASS one-column result at 390px — tracks=1
PASS evidence follows answer content at 390px
PASS first citation open by default
PASS evidence heading shows source count — Evidence 3 sources
PASS second citation toggles open on mobile
PASS desktop 1440 two-column answer+evidence — tracks=2
PASS hierarchy answer -> gaps -> suggestions -> evidence
PASS prefers-reduced-motion disables spinner animation — reduce=none normal=spin
PASS no console errors during flows
PASS no 4xx/5xx responses during flows

## Contrast (AC-11, computed from the OKLCH tokens via OKLab → sRGB → WCAG)

| Pair | Ratio | Verdict |
|---|---|---|
| text-primary on surface-page | 16.81:1 | AA |
| text-primary on surface-panel | 15.68:1 | AA |
| text-secondary on surface-page | 7.28:1 | AA |
| text-secondary on surface-panel | 6.79:1 | AA |
| text-secondary on surface-raised (duplicate badge) | 6.17:1 | AA |
| state-active links/focus on surface-page | 12.57:1 | AA |
| state-success on surface-panel (ready badge) | 9.28:1 | AA |
| state-warning on surface-panel (processing/incomplete) | 10.56:1 | AA |
| state-danger on surface-panel (failed/errors) | 6.29:1 | AA |
| state-danger on surface-raised (badge) | 5.71:1 | AA |
| button label (surface-page) on state-active | 12.57:1 | AA |

All pairs meet WCAG AA (≥4.5:1) on the actual surfaces where they render.

## Environment notes (verification honesty)

- The verification instance ran the worktree's FastAPI on 127.0.0.1:8001
  (port 8000 was occupied by the separate phase6-eval stack, which was left
  untouched), serving the worktree's `frontend/dist` production build, with
  runtime data in the session scratchpad.
- Qdrant (127.0.0.1:6333) is shared with the running phase6-eval stack, so
  live retrieval mixed this run's seed documents with pre-existing eval-corpus
  chunks (e.g. TechCorp content). This affects only answer/citation *content*
  in the screenshots, not any UI behavior under verification. UI verdicts are
  unaffected; RAG quality is out of scope for this task.
- The failed-row error text visible in screenshots includes an internal path
  returned verbatim by the backend — recorded as ADR 0018 (Proposed), not
  repaired in the UI.

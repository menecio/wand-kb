# AGENTS.md

This file is the standing contract for any agent (orchestrator or subagent) working
in this repository. Read it before doing anything else, then read the files it
points to.

## 1. Goal (source of truth)

The goal of this repository is to **fulfill the goals in `CHALLENGE.md`** —
Challenge #2, "AI-Powered Knowledge Base Search & Enrichment" (Wand AI take-home).

In scope (from `CHALLENGE.md`):

- Document upload & storage.
- Natural-language search over uploaded documents.
- AI-generated answers using the retrieved documents (RAG pipeline).
- Completeness check: detect missing/uncertain information.
- Enrichment suggestion: propose additional documents/data/actions to fill gaps.
- High marks: structured JSON output (`answer`, `confidence`, `missing_info`) and
  graceful handling of irrelevant documents.
- Stretch: auto-enrichment from a trusted external source; answer-quality rating.

`CHALLENGE.md` is the requirement source of truth. Do not silently narrow or
rewrite its goals; if a trade-off is needed, record it as an ADR (see §4) and
surface it to the user.

## 2. Mandatory process: follow the loop strictly

This repo uses a strict, append-only, multi-agent pipeline. **No ad-hoc coding.**
Every change must go through the loop defined in:

- `.opencode/README.md` — pipeline overview, stack, roles, workspace layout.
- `.opencode/agent/orchestrator.md` — phase-by-phase contract (authoritative).

The loop, in order, is non-negotiable:

1. **Worktree/Branch** — orchestrator creates worktree/branch in Phase 0 on `<type>/<slug>` and records in `brief.md`.
2. **Clarify** — ask until the brief is unambiguous; write `brief.md` under
   `.tasks/<YYYY-MM-DD>-<slug>/` (Objective, Scope, numbered Acceptance
   Criteria, Constraints, affected area, UI flag, stack URLs, Worktree, Branch, Base). Capture design
   decisions as Proposed ADRs. Do not proceed until the user confirms.
3. **Scaffold (if needed)** — if repo has no app code, delegate minimal scaffold to `implementer` before tests.
4. **Environment (UI only)** — bootstrap Playwright once if UI changes and no
   config exists.
5. **Issue** — `issue-creator` creates the GitHub issue from the brief.
6. **Tests** — `test-writer` writes TDD tests that must fail first; every active
   criterion gets a test and commits them.
7. **Implement** — `implementer` makes tests pass; never touches tests; runs lint/typecheck and commits with Conventional Commits.
8. **Verify** — `logic-verifier` always (runs both suites + criteria); plus
   `visual-verifier` in parallel when UI is involved.
9. **Loop** — on `CHANGES`: repeat-check (`REPEAT:` findings escalate on second
   appearance), decision-check (ADR before deviating), else append an
   `## Amendment N` to `brief.md` and re-implement. **Hard limit: 3 verification
   rounds** (`verify-1`, `verify-2`, `verify-3`); a 4th is never started.
   On the limit or a repeat, STOP and post an escalation report; wait for the
   user. A restarted pipeline uses a fresh `.tasks/` directory.
10. **Pull Request** — only when all verdicts are `PASS`: `pr-creator` opens a
   PR from the task branch to `main`, linking the issue and the evidence (branch must have commits).
11. **Close** — only when the PR is created: append closing event, summarize,
   link the issue, the PR, and the `.tasks/<dir>/` evidence path.

The orchestrator is the only primary agent. Subagents receive pointer-based
handoffs (pipeline path + iteration + short instruction) and read `brief.md`,
`log.md` and reports themselves. Passing the brief inline after the first
delegation is forbidden.

## 3. Roles (who may edit what)

| Agent | Edits |
|---|---|
| orchestrator | `.tasks/**` only |
| issue-creator | `.tasks/**` only (creates issue via `gh`) |
| test-writer | tests + `.tasks/**` |
| implementer | code (not tests) + `.tasks/**` |
| logic-verifier | `.tasks/**` only (read-only on code) |
| visual-verifier | `.tasks/**` only (read-only on code) |
| adr-writer | `docs/adr/**` + `.tasks/**` |
| playwright-setup | Playwright config, `package.json`, `e2e/`, `.gitignore`, `.tasks/**` |

The implementer never modifies tests. If a test looks wrong, it reports it and
the orchestrator decides whether an amendment is needed.

## 4. Evidence & decision rules (non-negotiable)

- All pipeline state lives in `.tasks/<YYYY-MM-DD>-<slug>/`: `brief.md`,
  `log.md`, `reports/`.
- **Append-only**: never edit or delete previously written lines. New sections
  are appended at the end, headed `## [YYYY-MM-DDTHH:MM] <author> — <event>`.
  Scope/criteria changes are written as amendments referencing prior sections.
- ADRs live in `docs/adr/` as `NNNN-<kebab-slug>.md` (MADR-lite: Context,
  Decision, Alternatives considered with rejection reasons, Consequences).
  Status starts `Proposed`; only the human flips it to `Accepted` (or
  `Superseded by NNNN`). Content is append-only except the Status line.
- Every brief amendment that changes a decision must reference the ADR number.
- `log.md` is the source of truth for the iteration count — never rely on memory.

## 5. Stack defaults (from `.opencode/README.md`)

- Backend: Python, tests with pytest, lint/typecheck via `uv run ruff` /
  `uv run mypy`. Dependencies managed with **uv** (`pyproject.toml` + `uv.lock`):
  use `uv add`, `uv sync`, `uv lock`, `uv run`. Never pip, pip3, or
  `requirements*.txt` / `Pipfile`.
- Frontend: TypeScript + React, tests with vitest, typecheck via `npx tsc` /
  `npm run build`.
- Runtime: everything in Docker Compose (`docker compose up`); tests run on the
  host against compose services.
- E2E/visual: Playwright in `e2e/`, `baseURL` from `E2E_BASE_URL`.
- Monorepo: one directory per component; brief lists affected component dirs and
  area (backend / frontend / both).

If the layout differs, update the edit globs in the agent files so the
test-writer/implementer deny-allow pairs stay mirrored.

## 6. Architecture rules (strict, non-negotiable)

Backend stack: **Python + FastAPI + Pydantic**. Keep it **simple as fuck** and
follow the Zen of Python: "Simple is better than complex."

Forbidden architectural styles/patterns (do NOT use, propose, or scaffold):

- Domain-Driven Design (DDD): no aggregates, entities, value objects, domain
  services, bounded contexts, ubiquitous language modeling.
- CQRS: no separate command/query models, no command/query handlers split.
- Repository pattern: no repository interfaces/abstractions over storage; call
  the DB/ORM/vector store directly from the service/route layer.
- Hexagonal architecture: no ports/adapters, no domain/application/infrastructure
  layering, no "clean architecture" folder trees.

Preferred style:

- Flat, procedural-ish modules: routers (`api/`), schemas (`schemas/`),
  services (`services/`), and storage helpers as plain functions/classes.
- FastAPI dependency injection for shared resources (DB session, settings, LLM
  client); Pydantic models for request/response/validation.
- Direct calls: route → service function → storage/LLM client. No indirection
  layers, no abstract base classes "for future extensibility", no factories
  unless genuinely needed.
- One module per concern, short files, obvious names. YAGNI: build only what the
  current acceptance criterion needs.

If a design genuinely needs one of the forbidden patterns, it must be raised to
the user as a decision (ADR with Status: Proposed) before implementation — never
introduced silently.

## 7. Git, worktrees & commits (strict, non-negotiable)

- **Worktrees are mandatory.** All implementation, test, and verification work
  happens in a dedicated git worktree, never in the main working tree. The
  orchestrator creates one per task (via `opencode.worktree_create` or
  `git worktree add`) on a new branch in Phase 0 before any delegation that touches code/tests. The branch name must be recorded in `brief.md`. The main worktree stays on `main` and is
  treated as read-only by agents.
- **Committing to `main` is forbidden.** If an agent finds itself on `main`,
  it must stop and create a worktree/branch first. Direct commits, force-pushes,
  resets, or merges targeting `main` are prohibited.
- Branch naming: `<type>/<slug>` where type is a conventional-commit type
  (feat, fix, docs, ...), e.g. `feat/kb-search`.
- **Conventional Commits are mandatory.** Every commit message follows the spec:
  `<type>(<scope>): <subject>` (scope optional), with types: feat, fix, docs,
  style, refactor, perf, test, build, ci, chore, revert. Subject in imperative
  mood, lowercase, no trailing period, ≤72 characters. Body explains *why*.
  Breaking changes use `!` after type/scope or a `BREAKING CHANGE:` footer.
- Commits are made inside the worktree on its branch; the main worktree never
  receives commits. Cleanup (`worktree_remove`) only after user confirms merge.
- **No merge commits.** Integrations into `main` must be done via rebase
  (fast-forward only): `git rebase <branch>` or `git merge --ff-only`. Never
  create a merge commit targeting `main`.
- Never rewrite published history; prefer new commits over amends on shared
  branches.

## 8. Hard rules for all agents

- Do not skip phases or run the implementer before tests exist.
- Do not modify tests to make them pass.
- The orchestrator writes ONLY under `.tasks/`. It must never create source
  code, data, fixtures, or config files; delegate those to implementer/
  test-writer.
- Tests are written only by `test-writer`; `implementer` never writes or
  edits tests, even if asked.
- Do not start a 4th verification round; escalate instead.
- Do not edit `CHALLENGE.md` or files under `.opencode/agent/` unless the user
  explicitly asks.
- Do not edit or delete prior content in `.tasks/` or `docs/adr/` (append only).
- Do not invent requirements beyond `CHALLENGE.md`; surface gaps to the user.
- Prefer structured JSON output (`answer`, `confidence`, `missing_info`) and
  graceful handling of irrelevant documents, per the challenge's high-marks bar.
- Lint and typecheck must pass before any commit: backend `uv run ruff` +
  `uv run mypy`, frontend `npx tsc --noEmit` + `npx eslint`. Enforced by the
  pre-commit hook and verified by logic-verifier.

## 9. Project state

As of the last commit, the repository contains only the agentic-loop scaffolding
(`.opencode/`, `opencode.json`, `pyproject.toml`) and `CHALLENGE.md` — no
application code yet. The first pipeline run must scaffold the prototype that
fulfills `CHALLENGE.md`. Model routing is configured in `opencode.json`.

## 10. Pointers

- Goal: `CHALLENGE.md`
- Pipeline: `.opencode/README.md`
- Orchestrator contract: `.opencode/agent/orchestrator.md`
- Subagent contracts: `.opencode/agent/{test-writer,implementer,logic-verifier,visual-verifier,issue-creator,adr-writer,playwright-setup}.md`
- Model routing: `opencode.json`
- Runtime deps: `pyproject.toml`
- Git hook (blocks commits on main): `.githooks/pre-commit` (core.hooksPath)

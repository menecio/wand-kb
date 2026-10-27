# Multi-agent pipeline for OpenCode (orchestrator + 5 subagents)

A pipeline with full auditability: all state lives in **append-only** `.md` files
under `.tasks/`, and handoffs between agents are file pointers, not regenerated text.

## Stack defaults (Python backend + React/TypeScript frontend)

The permission globs and allowed commands assume:

- **Backend**: Python, tests with **pytest** (`tests/`, `test_*.py`, `conftest.py`),
  linting/typechecking with `uv run ruff` / `uv run mypy`. Dependencies managed
  with **uv** (`pyproject.toml` + `uv.lock`): use `uv add`, `uv sync`, `uv lock`,
  `uv run`. Never pip, pip3, or `requirements*.txt` / `Pipfile`. If you use
  poetry or plain pip, replace the `uv run *` command globs with `poetry run pytest*`
  etc.
- **Frontend**: TypeScript + React, tests with **vitest** (`*.test.ts(x)`,
  `*.spec.ts(x)`), typechecking via `npx tsc` / `npm run build`.
- **Runtime**: everything runs in **Docker Compose** (`docker compose up`),
  so agents that need the app or backing services bring the stack up with
  `docker compose up -d` and check health with `docker compose ps`. Tests run
  on the host against the compose services.
- **E2E / visual**: **Playwright** tests in `e2e/`. If Playwright is not yet
  configured, the `playwright-setup` agent bootstraps it on the first UI task
  (Phase 1.5): it reads `docker-compose.yml` to discover the frontend URL,
  sets `baseURL` from `E2E_BASE_URL`, and configures `webServer` as
  `docker compose up -d` with `reuseExistingServer: true` — Playwright never
  runs `npm run dev`. It only runs once; afterwards the orchestrator skips it,
  and its report records the exact `E2E_BASE_URL` other agents reuse.
- Monorepo with one directory per component: the brief lists the component
  directories affected, and the brief records which area a task affects
  (backend / frontend / both). The orchestrator always runs both suites
  (pytest + vitest) in verification.

If your layout differs (e.g. a `frontend/` folder instead of a single root),
adjust the edit globs accordingly — the deny/allow pairs in `test-writer` and
`implementer` must stay mirrored so only one of them can touch tests.

## Install

Copy the `.opencode/agent/` folder to your repo root (or the files to
`~/.config/opencode/agent/` if you want them globally). Requires an authenticated
`gh` CLI for the issue agent.

## Roles

| Agent | Mode | Purpose | Can edit |
|---|---|---|---|
| `orchestrator` | primary | Asks questions, writes the brief, runs the loop | `.tasks/**` only |
| `issue-creator` | subagent | Creates the GitHub Issue via `gh` | nothing |
| `test-writer` | subagent | Writes TDD tests (pytest + vitest) that fail first | tests + `.tasks/**` |
| `implementer` | subagent | Implements without touching tests | code, **not** tests |
| `logic-verifier` | subagent | Checks criteria vs implementation, runs both suites | `.tasks/**` only |
| `visual-verifier` | subagent | Checks UI changes with Playwright (when applicable) | `.tasks/**` only |
| `adr-writer` | subagent | Records decisions as ADRs in `docs/adr/` | `docs/adr/**` + `.tasks/**` |
| `playwright-setup` | subagent | One-time Playwright bootstrap (config + smoke test) | Playwright config, package.json, `e2e/`, `.gitignore` |

## Workspace layout

Each task creates:

```
.tasks/2026-10-21-csv-export/
  brief.md            # original brief + amendments (append-only)
  log.md              # pipeline event log (append-only)
  reports/
    issue.md          # issue number and URL
    tests-1.md        # test-writer report (iteration 1)
    impl-1.md         # implementer report
    verify-1-logic.md # logic verifier verdict
    verify-1-visual.md# visual verifier verdict (when applicable)
    ...
```

**Evidence rule**: no agent edits or deletes previous lines under `.tasks/`.
New sections are only appended at the end, each headed with a timestamp and
author. Changes are recorded as amendments that reference what came before,
so the full history can be reconstructed by reading the files top to bottom.

## The loop

1. **Phase 0**: Orchestrator creates worktree/branch on `<type>/<slug>` and records it in `brief.md`.
2. Orchestrator asks the user until the brief is unambiguous → writes/updates `brief.md`. If repo has no app code, delegates scaffold to `implementer`.
3. `issue-creator` creates the issue.
4. `test-writer` writes tests encoding the criteria (they must fail first) and commits them.
5. `implementer` implements until tests pass, runs lint/typecheck, and commits with Conventional Commits.
6. `logic-verifier` always; `visual-verifier` if there are UI changes. Both can run in parallel.
7. If any verdict is `CHANGES`, the orchestrator records an amendment in `brief.md`
   and goes back to step 5.
8. Loop safeguards against infinite verify→implement cycles:
   - The round counter lives in `log.md`, not in the model's memory.
   - HARD LIMIT: 3 verification rounds; a 4th is never started.
   - Verifiers prefix findings that remain unresolved from earlier rounds
     with `REPEAT:`; a second appearance of a `REPEAT` finding escalates
     immediately instead of burning another round.
   - On hitting the limit or a repeat, the orchestrator STOPS and posts an
     escalation report (criterion status, pending findings, diagnosis, options)
     and waits for the user. A restarted pipeline uses a fresh `.tasks/` dir.
9. Only when all verdicts are `PASS` does it open a PR (via `pr-creator`) from
   the task branch to `main`, linking the issue and the evidence. The branch must have commits.
10. Then it closes out.

## Decision records (ADRs)

Decisions are captured by the `adr-writer` subagent at three points:

1. **During clarification**: architectural/design decisions surfaced by the
   questions (library choices, patterns, data model, tradeoffs) are drafted as
   `Status: Proposed` ADRs and shown to the user as part of brief confirmation.
2. **Mid-loop**: if resolving verifier findings requires deviating from the
   brief or a real tradeoff, the orchestrator delegates to `adr-writer` BEFORE
   writing the amendment, and the amendment references the ADR number.
3. **On escalation**: if the blocker is a genuine design dilemma, a `Proposed`
   ADR is drafted as part of the escalation report so the user can decide
   with full context.

Format is MADR-lite (`NNNN-<slug>.md` in `docs/adr/`): Context, Decision,
Alternatives considered (with rejection reasons), Consequences. Content is
append-only except the `Status` line (`Proposed → Accepted`, or
`Superseded by NNNN` via a new ADR — reversed decisions are never rewritten).
Only the human turns `Proposed` into `Accepted`.

## How context travels

- Subagents start with fresh context: the only thing they receive is the `prompt`
  of the Task tool call.
- The orchestrator uses short handoffs: pipeline path + iteration + a specific
  instruction. Each agent reads `brief.md`, `log.md` and previous reports itself.
- The code and `git diff` are the shared source of truth; nobody relies on summaries.

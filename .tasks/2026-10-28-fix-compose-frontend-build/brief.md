# Brief — docker compose up must serve the frontend without a host build step

## [2026-10-28T09:16] orchestrator — brief v1 (draft, pending user confirmation)

### Objective

After a fresh clone, a single `docker compose up` (with `--build`) must bring up the
full application — including the React UI served from http://127.0.0.1:8000/ —
without any manual host-side build step (no `npm ci`, no `npm run build`).

### Problem (diagnosed by orchestrator, read-only)

- `backend/app/main.py` mounts `frontend/dist` as static files at `/`, but only
  if `frontend/dist/index.html` exists.
- `docker-compose.yml` bind-mounts `./frontend/dist` (read-only) into the
  backend container at `/app/frontend/dist`.
- `frontend/dist` is gitignored and nothing in the compose stack ever builds it.
  On a fresh clone the mount is empty → the static mount is skipped → `GET /`
  returns 404 and the UI never loads.
- `README.md` ("Running the Application") promises that `docker compose up -d`
  alone yields the app on http://127.0.0.1:8000, which is currently false.

### Scope

In:

- Make the packaged runtime self-contained: the UI must be built as part of the
  Docker build/compose flow (frontend build must not depend on artifacts on the
  host).
- Keep the same-origin serving design (backend serves the built frontend, no
  CORS, no separate frontend service).
- Update `README.md` so the documented startup commands match reality.
- ADR for the chosen packaging approach (Status: Proposed, human accepts).

Out:

- No UI/visual/behavior changes to the React app itself.
- No changes to API contracts, retrieval, or generation logic.
- No dev-mode workflow changes (`npm run dev` keeps working as-is).

### Acceptance criteria (numbered, verifiable)

1. From a clean state (no `frontend/dist`, no `node_modules` on host),
   `docker compose up -d --build` produces a stack where `GET /` returns 200
   with the built React app's `index.html`, and its JS/CSS assets load.
2. No host-side npm/node step is required to get criterion 1.
3. Existing behavior unchanged: `/api/*` endpoints, `/docs`, and the ollama /
   qdrant services keep working as before.
4. README "Running the Application" documents the exact working commands
   (including `--build` and any first-run notes such as model pulls).
5. Tests encode the contract (e.g. compose/Dockerfile assertions and/or an
   integration check that `/` serves HTML after a clean build); tests fail
   before the fix and pass after.

### Constraints

- Stack rules from AGENTS.md §5/§6: FastAPI + Pydantic backend, flat/simple
  design, Docker Compose runtime, no forbidden architecture patterns.
- `uv` for backend deps; npm for frontend deps (build happens in Docker).
- Append-only `.tasks/`; conventional commits on the task branch only.
- Lint/typecheck must pass before commits (backend ruff+mypy, frontend
  tsc+eslint where touched).

### Affected area

both (backend packaging + frontend build wiring; no frontend UI code changes)

### Component directories affected

- `backend/` (Dockerfile)
- `frontend/` (build context only, no source changes expected)
- root: `docker-compose.yml`, `README.md`

### Involves UI changes?

no (no screens/components change; only how the built UI is produced/served)

### Stack URLs

- Frontend/UI: http://127.0.0.1:8000/ (served by backend, same origin)
- Backend API: http://127.0.0.1:8000/docs
- Qdrant: http://127.0.0.1:6333
- Ollama: http://127.0.0.1:11434

### Worktree

/Users/menecio/code/wand-take-home-fix-compose-frontend-build

### Branch

fix/compose-frontend-build

### Base

main

### Proposed ADRs (decision capture — to be drafted by adr-writer)

- ADR-0019 (proposed): Frontend packaging approach — options:
  (a) multi-stage backend Dockerfile builds the frontend inside the image
  (node stage → `npm ci && npm run build` → copy dist into final image);
  (b) compose `frontend` build service (node image) writing to a shared
  bind mount before `app` starts; (c) keep bind mount, document manual
  `npm run build`. Orchestrator recommends (a): single-command reproducible
  runtime, no host artifacts, no start-ordering race.

## [2026-10-28T09:18] orchestrator — brief v1 confirmed by user (multi-stage Dockerfile)

User selected approach (a): multi-stage backend Dockerfile. `adr-writer` will draft ADR-0019 as Proposed; no scope change otherwise. Brief v1 is locked; proceeding to issue → tests → implement → verify.


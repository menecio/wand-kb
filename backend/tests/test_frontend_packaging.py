"""Packaging contract: compose + Dockerfile must build the frontend in-image.

A fresh clone has no frontend/dist (gitignored). The UI must be produced by
`docker compose up --build` without a host-side npm step. This is enforced by
checking the committed compose/Dockerfile/README contracts (unit tests, no
compose up required).

Failing before the fix is intentional (TDD, Phase 3).
"""

from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
COMPOSE_PATH = REPO_ROOT / "docker-compose.yml"
DOCKERFILE_PATH = REPO_ROOT / "backend" / "Dockerfile"
README_PATH = REPO_ROOT / "README.md"


def _load_compose() -> dict:
    text = COMPOSE_PATH.read_text(encoding="utf-8")
    return yaml.safe_load(text)


def _dockerfile_text() -> str:
    return DOCKERFILE_PATH.read_text(encoding="utf-8")


def test_compose_does_not_depend_on_host_frontend_dist_bind_mount() -> None:
    """The app service must not rely on ./frontend/dist from the host."""
    data = _load_compose()
    app = data["services"]["app"]
    volumes: list[str] = app.get("volumes") or []
    # No entry may reference frontend/dist (bind mount from host)
    assert not any("frontend/dist" in v for v in volumes), (
        "compose app service still bind-mounts host frontend/dist: "
        f"{volumes} — the image must be self-contained"
    )


def test_compose_app_build_uses_repo_root_context_with_backend_dockerfile() -> None:
    """Multi-stage build requires context at repo root so the frontend stage can copy source."""
    data = _load_compose()
    build = data["services"]["app"]["build"]
    assert isinstance(build, dict), f"expected app.build as mapping (context + dockerfile), got {type(build)}: {build!r}"
    dockerfile = build.get("dockerfile", "")
    context = build.get("context", "")
    assert "backend" in dockerfile and "Dockerfile" in dockerfile, f"unexpected dockerfile {dockerfile!r}"
    # Context "." or "./" or "" relative to repo root; tolerate "./" form
    normalized = context.strip()
    assert normalized in (".", "./", ""), f"expected build.context at repo root, got {context!r}"


def test_dockerfile_is_multi_stage_building_frontend() -> None:
    """Backend Dockerfile must have a node stage that builds frontend and copies dist to final image."""
    text = _dockerfile_text()
    lower = text.lower()
    # Node/frontend stage exists and runs the frontend build
    assert "from node:" in lower or "from node@" in lower, "missing node-based frontend build stage"
    assert "frontend" in lower, "Dockerfile does not reference frontend"
    assert "npm" in lower and ("vite build" in lower or "npm run build" in lower), (
        "Dockerfile frontend stage must run npm + vite build"
    )
    # Dist copied into final image (frontend/dist)
    assert "frontend/dist" in text or "frontend\\dist" in text, "Dockerfile must COPY the built frontend/dist into final image"
    # Multi-stage signal: at least two FROM lines
    assert lower.count("from ") >= 2, "expected multi-stage Dockerfile with >= 2 FROM lines"


def test_readme_documents_compose_up_with_build() -> None:
    """README must tell users to run compose with --build so the baked image is used."""
    readme = README_PATH.read_text(encoding="utf-8")
    assert "docker compose up" in readme
    # Must mention --build somewhere near the Running section so a fresh clone works
    assert "--build" in readme, "README must include `--build` in the docker compose startup command"

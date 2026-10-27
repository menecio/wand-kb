"""Persistent JSON document registry with atomic writes."""

from __future__ import annotations

import contextlib
import json
import os
from pathlib import Path
from typing import Any

from app.config import settings

# Public attribute kept for tests that monkeypatch it directly.
REGISTRY_PATH = Path(settings.registry_path).resolve()
_INITIAL_REGISTRY_PATH = REGISTRY_PATH


def _registry_path() -> Path:
    """Return the active registry path.

    Production uses the configured settings value. Tests that patch
    ``settings.registry_path`` or ``REGISTRY_PATH`` directly are both supported:
    a changed ``settings.registry_path`` takes precedence, otherwise the patched
    ``REGISTRY_PATH`` is used.
    """
    current = Path(settings.registry_path).resolve()
    if current != _INITIAL_REGISTRY_PATH:
        return current
    return REGISTRY_PATH


def load_registry() -> dict[str, Any]:
    """Load the document registry from disk, returning an empty dict if absent."""
    path = _registry_path()
    if not path.exists():
        return {}

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}

    if not isinstance(data, dict):
        return {}
    return data


def save_registry(registry: dict[str, Any]) -> None:
    """Persist the registry atomically using temp-file + rename."""
    path = _registry_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(".tmp")

    try:
        temp_path.write_text(
            json.dumps(registry, indent=2, default=str),
            encoding="utf-8",
        )
        os.replace(temp_path, path)
    except Exception:
        with contextlib.suppress(OSError):
            temp_path.unlink(missing_ok=True)
        raise

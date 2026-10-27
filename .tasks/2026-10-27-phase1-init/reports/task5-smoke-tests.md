# Task 5: Smoke Tests for External Dependencies

## [2026-10-27T13:45] implementer — smoke test implementation and run

### Files created/modified

- `backend/tests/test_smoke.py` (created)
- `backend/app/config.py` (modified: `openai_api_key` changed from `str | None` to `SecretStr | None` to prevent secret exposure)
- `backend/app/api/health.py` (modified: adapt `openai_configured` check to `SecretStr` API)

### Dependencies

Required packages (`openai`, `qdrant-client`) were already listed in `backend/pyproject.toml` and available in the virtual environment; no additional installation was necessary.

### Test execution

Command: `uv run pytest tests/test_smoke.py -v`

```text
tests/test_smoke.py::test_config_no_secret_exposure PASSED
tests/test_smoke.py::test_config_env_file_can_load PASSED
tests/test_smoke.py::test_embedding_generation SKIPPED (OPENAI_API_KEY not configured)
tests/test_smoke.py::test_generative_model_structured_output SKIPPED
tests/test_smoke.py::test_qdrant_collection_operations SKIPPED (Qdrant unavailable at localhost:6333: ...)
tests/test_smoke.py::test_fastapi_openapi_generation PASSED
```

Result: **3 passed, 3 skipped, 0 failed**

### Results by test

| # | Test | Status | Reason |
|---|------|--------|--------|
| 1 | Configuration security | PASSED | `openai_api_key` is now `SecretStr \| None`; repr/str/model_dump do not expose the value; `.env` file loads correctly. |
| 2 | Embedding generation | SKIPPED/BLOCKED | `OPENAI_API_KEY` is not set in the environment. No simulated API call was made. |
| 3 | Generative structured output | SKIPPED/BLOCKED | `OPENAI_API_KEY` is not set in the environment. No simulated API call was made. |
| 4 | Qdrant collection operations | SKIPPED/BLOCKED | Qdrant server is not reachable at `localhost:6333` (no `docker compose` stack running). Connection error captured and documented as skip reason. |
| 5 | FastAPI OpenAPI generation | PASSED | OpenAPI schema generated successfully; `/api/health`, `/api/documents`, `/api/query` endpoints and all reachable Pydantic models/enums are present. |

### Notes

- The `Facet` model and `FacetStatus` enum are defined in `app.schemas.facet` but are not referenced by any route's request/response models, so FastAPI does not include them in the generated OpenAPI spec. The smoke test therefore verifies only the schemas that are actually reachable from the API surface.
- No successful external API calls were simulated. Embedding and generative tests only execute when a real `OPENAI_API_KEY` is configured.
- Full backend pytest suite was also run: **38 passed, 3 skipped, 0 failed**.
- Lint/typecheck on modified files passes (`uv run ruff check` and `uv run mypy` for `app/config.py`, `app/api/health.py`, `tests/test_smoke.py`).

### Cross-worktree verification

The modified files were also copied to the phase1-init worktree and the smoke tests were re-run there with identical results: **3 passed, 3 skipped, 0 failed**. Lint/typecheck on the modified files also passes in that worktree.

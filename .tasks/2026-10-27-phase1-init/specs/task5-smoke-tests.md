# Task 5 Specification: Smoke Tests

## Objective
Verify external dependencies and configuration with minimal, independent checks.

## Test Requirements

### Test 1: Configuration Security
- Load Settings from environment
- Verify OPENAI_API_KEY is not logged or exposed in error messages
- Verify API key is Optional (None is acceptable)
- Test that .env file can be loaded if present

### Test 2: Test Embedding Generation
- Attempt to generate a test embedding using OpenAI API
- Use a minimal request: "test"
- Expected model: text-embedding-3-small (or configured model)
- Expected dimensions: 1536 (or configured dimensions)
- **If OPENAI_API_KEY is missing**: Mark as BLOCKED, do not simulate success

### Test 3: Generative Model Structured Output
- Attempt to generate structured output using OpenAI API
- Use a minimal prompt: "Return a JSON object with key 'test' and value 'passed'"
- Verify response conforms to a simple schema
- Expected model: gpt-4o-mini (or configured model)
- **If OPENAI_API_KEY is missing**: Mark as BLOCKED, do not simulate success

### Test 4: Qdrant Collection Operations
- Create a Qdrant client (local or cloud based on config)
- Create a test collection with small dimensions (e.g., 128)
- Verify collection exists
- Delete the test collection
- Verify deletion succeeded
- **If Qdrant is not available**: Mark as BLOCKED, document the error

### Test 5: FastAPI OpenAPI Generation
- Import the FastAPI app
- Generate OpenAPI schema
- Verify all models and enums are present
- Verify endpoints are documented
- This should always succeed (no external dependencies)

## Implementation

Create `backend/tests/test_smoke.py` with the following structure:

```python
import pytest
from app.config import Settings
from app.main import app

def test_config_no_secret_exposure():
    """Verify API key is not exposed in string representations."""
    settings = Settings()
    # Test that API key is not in repr/str
    assert settings.openai_api_key not in repr(settings) or settings.openai_api_key is None
    
def test_embedding_generation():
    """Test embedding generation (blocked if no API key)."""
    settings = Settings()
    if settings.openai_api_key is None:
        pytest.skip("OPENAI_API_KEY not configured")
    # Attempt to generate embedding
    # Record result or error
    
def test_generative_model_structured_output():
    """Test structured output generation (blocked if no API key)."""
    settings = Settings()
    if settings.openai_api_key is None:
        pytest.skip("OPENAI_API_KEY not configured")
    # Attempt to generate structured output
    # Record result or error
    
def test_qdrant_collection_operations():
    """Test Qdrant collection create/delete."""
    # Create test collection
    # Verify it exists
    # Delete it
    # Verify deletion
    
def test_fastapi_openapi_generation():
    """Verify OpenAPI schema can be generated."""
    # Generate schema
    # Verify models present
    # Verify endpoints present
```

## Verification Criteria

After running tests, report:
1. Which tests passed
2. Which tests were skipped/blocked (with reason)
3. Which tests failed (with exact error)
4. Do NOT simulate successful external API calls
5. Do NOT switch providers or models without identifying root cause

## Acceptance Criteria

- [ ] Configuration test passes (no secret exposure)
- [ ] Embedding test passes OR is properly blocked with clear reason
- [ ] Generative model test passes OR is properly blocked with clear reason
- [ ] Qdrant test passes OR is blocked with error documented
- [ ] FastAPI OpenAPI test passes (always expected to pass)
- [ ] All test results are documented in the report
- [ ] No simulated successful external calls

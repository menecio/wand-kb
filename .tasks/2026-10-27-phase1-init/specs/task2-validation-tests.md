# Task 2 Specification: Validation Tests

## Objective
Create comprehensive validation tests for Pydantic models to verify integrity rules.

## Location
`backend/tests/test_validation.py`

## Test Requirements

### IR-1: Factual Answers Require Valid Citations
Test that QueryResponse with factual answer but empty citations is invalid unless confidence is INSUFFICIENT_DATA.

### IR-2: Answered Facets Require Evidence
Test that Facet with status ANSWERED must have non-empty citation_ids.

### IR-3: Completeness Implies No Material Gaps
Test that when is_complete=True, missing_info must be empty.

### IR-4: INSUFFICIENT_DATA Implies Incomplete
Test that confidence=INSUFFICIENT_DATA requires is_complete=False.

### IR-5: Citation Relevance Score Range
Test that Citation.relevance_score must be between 0.0 and 1.0.

### IR-6: Document Status Values
Test that DocumentSummary.status only accepts PROCESSING, READY, or FAILED.

### IR-7: Facet Status Values
Test that Facet.status only accepts ANSWERED, PARTIAL, MISSING, UNCERTAIN, or CONFLICTING.

### IR-8: Confidence Level Values
Test that QueryResponse.confidence only accepts HIGH, MEDIUM, LOW, or INSUFFICIENT_DATA.

### IR-9: Action Type Values
Test that EnrichmentSuggestion.action_type only accepts UPLOAD_DOCUMENT, QUERY_EXTERNAL_SYSTEM, or ASK_USER.

### IR-10: QueryRequest Validation
Test that QueryRequest.question must not be empty.

### Valid Instance Tests
Create tests with valid instances of each model to ensure they can be instantiated correctly:
- Valid QueryRequest
- Valid QueryResponse with all fields
- Valid Citation with all fields
- Valid EnrichmentSuggestion
- Valid DocumentSummary
- Valid Facet

### Invalid Instance Tests
Create tests with invalid instances to ensure validation errors are raised:
- Citation with relevance_score > 1.0
- Citation with relevance_score < 0.0
- QueryRequest with empty question
- DocumentSummary with invalid status
- Facet with invalid status

## Implementation Notes
- Use pytest for all tests
- Import models from app.schemas
- Use pytest.raises for validation errors
- Test both valid and invalid cases
- Each test should be independent and focused on a single invariant

## Verification
Run: `cd backend && python -m pytest tests/test_validation.py -v`
Expected: All tests pass

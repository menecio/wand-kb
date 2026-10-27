import uuid

from fastapi import APIRouter

from ..schemas.query import ConfidenceLevel, QueryRequest, QueryResponse

router = APIRouter()


@router.post("/api/query", response_model=QueryResponse)
async def query_knowledge_base(request: QueryRequest) -> QueryResponse:
    """Query the knowledge base with a natural language question."""
    # TODO: Implement RAG pipeline
    # This is a stub that returns an INSUFFICIENT_DATA response
    return QueryResponse(
        response_id=str(uuid.uuid4()),
        answer="RAG pipeline not yet implemented",
        confidence=ConfidenceLevel.INSUFFICIENT_DATA,
        is_complete=False,
        missing_info=["Full RAG pipeline implementation"],
        enrichment_suggestions=[],
        citations=[],
    )

"""Search and question-answering endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException

from app.schemas.facet import Facet, FacetStatus
from app.schemas.query import (
    ActionType,
    ConfidenceLevel,
    EnrichmentSuggestion,
    QueryRequest,
    QueryResponse,
    SearchRequest,
    SearchResponse,
    SearchResult,
)
from app.services.ollama import OllamaConnectionError
from app.services.qdrant import QdrantConnectionError
from app.services.query_pipeline import generate_answer, generate_query_embedding, retrieve_chunks

router = APIRouter()


def _normalize_chunk(chunk: dict) -> dict:
    """Normalize a retrieved chunk so it includes a top-level text key."""
    metadata = chunk.get("metadata", {})
    return {
        "id": chunk["id"],
        "text": metadata.get("text", ""),
        "score": chunk.get("score", 0.0),
        "metadata": metadata,
    }


@router.post("/api/search", response_model=SearchResponse)
async def search_knowledge_base(request: SearchRequest) -> SearchResponse:
    """Search the knowledge base for chunks relevant to the query."""
    try:
        query_vector = await generate_query_embedding(request.query)
        chunks = await retrieve_chunks(query_vector, top_k=request.top_k)
    except (OllamaConnectionError, QdrantConnectionError) as exc:
        raise HTTPException(status_code=503, detail=f"Search service unavailable: {exc}") from exc

    results = [
        SearchResult(
            chunk_id=chunk["id"],
            document_id=chunk["metadata"].get("document_id", ""),
            document_name=chunk["metadata"].get("source", ""),
            section=chunk["metadata"].get("section"),
            excerpt=chunk["metadata"].get("text", ""),
            score=chunk.get("score", 0.0),
        )
        for chunk in chunks
    ]

    return SearchResponse(results=results)


@router.post("/api/query", response_model=QueryResponse)
async def query_knowledge_base(request: QueryRequest) -> QueryResponse:
    """Query the knowledge base with a natural language question."""
    if not request.question.strip():
        raise HTTPException(status_code=422, detail="Question cannot be empty or whitespace only")

    try:
        query_vector = await generate_query_embedding(request.question)
        retrieved_chunks = await retrieve_chunks(query_vector)
    except (OllamaConnectionError, QdrantConnectionError) as exc:
        # Controlled early-exit response when retrieval services are unavailable.
        return _controlled_service_error_response(str(exc))

    context_chunks = [_normalize_chunk(chunk) for chunk in retrieved_chunks]
    return await generate_answer(request.question, context_chunks=context_chunks)


def _controlled_service_error_response(message: str) -> QueryResponse:
    """Return a non-factual INSUFFICIENT_DATA response when retrieval fails."""
    return QueryResponse(
        response_id=str(uuid.uuid4()),
        answer="Sufficient evidence could not be retrieved due to a service issue. "
        "Please try again after the service recovers.",
        confidence=ConfidenceLevel.INSUFFICIENT_DATA,
        is_complete=False,
        missing_info=["Retrieval service is currently unavailable."],
        enrichment_suggestions=[
            EnrichmentSuggestion(
                action_type=ActionType.ASK_USER,
                target="System operator",
                reason="The retrieval service returned an error; retrying may help.",
            )
        ],
        citations=[],
        facets=[
            Facet(
                description="Answer the question from retrieved evidence",
                status=FacetStatus.MISSING,
                citation_ids=[],
                associated_gap="Retrieval service is currently unavailable.",
            )
        ],
    )

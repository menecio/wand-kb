"""Search and question-answering endpoints."""

from fastapi import APIRouter

from app.schemas.query import (
    QueryRequest,
    QueryResponse,
    SearchRequest,
    SearchResponse,
    SearchResult,
)
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
    query_vector = await generate_query_embedding(request.query)
    chunks = await retrieve_chunks(query_vector, top_k=request.top_k)

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
    query_vector = await generate_query_embedding(request.question)
    retrieved_chunks = await retrieve_chunks(query_vector, top_k=5)
    context_chunks = [_normalize_chunk(chunk) for chunk in retrieved_chunks]

    return await generate_answer(request.question, context_chunks=context_chunks)

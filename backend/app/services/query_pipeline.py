"""RAG query pipeline: embed, retrieve, generate structured answer."""

import uuid
from typing import Any

from app.config import settings
from app.schemas.query import Citation, ConfidenceLevel, EnrichmentSuggestion, QueryResponse
from app.services.ollama import OllamaClient
from app.services.qdrant import QdrantClient

ollama_client = OllamaClient(base_url=settings.ollama_base_url)
qdrant_client = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)


async def generate_query_embedding(question: str) -> list[float]:
    """Generate an embedding vector for the question."""
    return ollama_client.generate_embedding(
        model=settings.ollama_embedding_model,
        text=question,
    )


async def retrieve_chunks(query_vector: list[float], top_k: int = 5) -> list[dict]:
    """Retrieve the top-k most similar chunks from Qdrant."""
    return qdrant_client.search(
        collection_name=settings.qdrant_collection_name,
        query_vector=query_vector,
        limit=top_k,
    )


def _build_prompt(question: str, context_chunks: list[dict]) -> str:
    """Build a prompt that asks the model to answer from the provided context."""
    context = "\n\n".join(
        f"[chunk {i}] source: {chunk['metadata'].get('source', 'unknown')}, "
        f"section: {chunk['metadata'].get('section', 'unknown')}\n{chunk['text']}"
        for i, chunk in enumerate(context_chunks)
    )

    if not context:
        context = "No relevant documents were found."

    return (
        "You are a helpful assistant that answers questions based only on the provided context. "
        "Return a JSON object with the following fields:\n"
        "- answer: a concise answer to the question\n"
        "- confidence: one of HIGH, MEDIUM, LOW, INSUFFICIENT_DATA\n"
        "- missing_info: a list of strings describing any missing information\n"
        "- citations: a list of objects with chunk_id, document_name, section, excerpt, and relevance_score\n\n"
        f"Question: {question}\n\n"
        f"Context:\n{context}\n\n"
        "Respond with valid JSON only."
    )


def _coerce_confidence(value: Any) -> ConfidenceLevel:
    """Convert a string or enum value to a ConfidenceLevel."""
    if isinstance(value, ConfidenceLevel):
        return value
    return ConfidenceLevel(str(value))


def _coerce_citations(value: Any) -> list[Citation]:
    """Convert a list of citation-like objects to Citation instances."""
    if not value:
        return []
    citations: list[Citation] = []
    for item in value:
        if isinstance(item, Citation):
            citations.append(item)
        else:
            citations.append(Citation.model_validate(item))
    return citations


def _coerce_enrichment_suggestions(value: Any) -> list[EnrichmentSuggestion]:
    """Convert a list of enrichment-like objects to EnrichmentSuggestion instances."""
    if not value:
        return []
    suggestions: list[EnrichmentSuggestion] = []
    for item in value:
        if isinstance(item, EnrichmentSuggestion):
            suggestions.append(item)
        else:
            suggestions.append(EnrichmentSuggestion.model_validate(item))
    return suggestions


async def generate_answer(question: str, context_chunks: list[dict]) -> QueryResponse:
    """Generate a structured answer with citations from the retrieved chunks."""
    prompt = _build_prompt(question, context_chunks)

    class _AnswerSchema(QueryResponse):
        """Temporary schema for structured generation."""

    try:
        result = ollama_client.generate_structured(
            model=settings.ollama_generation_model,
            prompt=prompt,
            schema=_AnswerSchema,
        )
    except Exception:
        # Fall back to a safe, deterministic response when generation fails.
        return QueryResponse(
            response_id=str(uuid.uuid4()),
            answer="I cannot answer this question based on the available information.",
            confidence=ConfidenceLevel.INSUFFICIENT_DATA,
            is_complete=False,
            missing_info=["Unable to generate an answer from the retrieved context."],
            enrichment_suggestions=[],
            citations=[],
        )

    context_ids = {chunk["id"] for chunk in context_chunks}
    citations = _coerce_citations(result.citations)
    valid_citations = [citation for citation in citations if citation.chunk_id in context_ids]

    confidence = _coerce_confidence(result.confidence)
    missing_info = list(result.missing_info) if result.missing_info else []

    # Enforce schema integrity: non-INSUFFICIENT_DATA answers require citations.
    if confidence != ConfidenceLevel.INSUFFICIENT_DATA and not valid_citations:
        confidence = ConfidenceLevel.INSUFFICIENT_DATA
        missing_info.append("No valid citations were returned for the answer.")

    is_complete = not (
        confidence == ConfidenceLevel.INSUFFICIENT_DATA or missing_info
    )

    response_id = result.response_id if isinstance(result.response_id, str) else str(uuid.uuid4())
    enrichment_suggestions = _coerce_enrichment_suggestions(
        result.enrichment_suggestions if result.enrichment_suggestions else []
    )

    return QueryResponse(
        response_id=response_id,
        answer=str(result.answer),
        confidence=confidence,
        is_complete=is_complete,
        missing_info=missing_info,
        enrichment_suggestions=enrichment_suggestions,
        citations=valid_citations,
    )

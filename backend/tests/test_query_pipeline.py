"""Tests for the RAG query pipeline."""

from unittest.mock import MagicMock, patch

import pytest

from app.schemas.query import Citation, QueryResponse
from app.services.query_pipeline import (
    generate_answer,
    generate_query_embedding,
    retrieve_chunks,
)


@pytest.fixture
def sample_chunks() -> list[dict]:
    """Small set of retrieved chunks for unit tests."""
    return [
        {
            "id": "chunk-1",
            "text": "The recovery time objective is 1 hour.",
            "score": 0.95,
            "metadata": {
                "source": "vertical_slice_fixture.md",
                "section": "Disaster Recovery",
                "chunk_index": 0,
            },
        },
        {
            "id": "chunk-2",
            "text": "The recovery point objective is 5 minutes.",
            "score": 0.87,
            "metadata": {
                "source": "vertical_slice_fixture.md",
                "section": "Disaster Recovery",
                "chunk_index": 1,
            },
        },
    ]


@pytest.mark.asyncio
async def test_generate_query_embedding_returns_vector() -> None:
    """generate_query_embedding returns a list of floats."""
    with patch("app.services.query_pipeline.ollama_client") as mock_ollama:
        mock_ollama.generate_embedding.return_value = [0.1] * 768
        vector = await generate_query_embedding("What is the RTO?")

    assert isinstance(vector, list)
    assert len(vector) == 768
    assert all(isinstance(v, float) for v in vector)


@pytest.mark.asyncio
async def test_generate_query_embedding_uses_embedding_model() -> None:
    """generate_query_embedding uses the configured embedding model."""
    with patch("app.services.query_pipeline.ollama_client") as mock_ollama:
        mock_ollama.generate_embedding.return_value = [0.0] * 768
        await generate_query_embedding("Acme disaster recovery")

    mock_ollama.generate_embedding.assert_called_once()
    call_kwargs = mock_ollama.generate_embedding.call_args.kwargs
    assert call_kwargs["model"] == "nomic-embed-text"


@pytest.mark.asyncio
async def test_retrieve_chunks_returns_chunks_with_scores() -> None:
    """retrieve_chunks returns scored chunks from Qdrant."""
    with patch("app.services.query_pipeline.qdrant_client") as mock_qdrant:
        mock_qdrant.search.return_value = [
            {
                "id": "chunk-1",
                "score": 0.95,
                "metadata": {"source": "doc.md", "chunk_index": 0},
            },
        ]
        results = await retrieve_chunks(query_vector=[0.1] * 768, top_k=5)

    assert isinstance(results, list)
    assert len(results) == 1
    assert results[0]["id"] == "chunk-1"
    assert results[0]["score"] == pytest.approx(0.95)


@pytest.mark.asyncio
async def test_retrieve_chunks_uses_top_k() -> None:
    """retrieve_chunks passes top_k to the vector store."""
    with patch("app.services.query_pipeline.qdrant_client") as mock_qdrant:
        mock_qdrant.search.return_value = []
        await retrieve_chunks(query_vector=[0.1] * 768, top_k=5)

    mock_qdrant.search.assert_called_once()
    assert mock_qdrant.search.call_args.kwargs["limit"] == 5


@pytest.mark.asyncio
async def test_generate_answer_returns_structured_response(sample_chunks: list[dict]) -> None:
    """generate_answer returns a QueryResponse with answer, confidence, and missing_info."""
    fake_response = MagicMock()
    fake_response.answer = "1 hour"
    fake_response.confidence = "HIGH"
    fake_response.missing_info = []
    fake_response.citations = []

    with patch("app.services.query_pipeline.ollama_client") as mock_ollama:
        mock_ollama.generate_structured.return_value = fake_response
        response = await generate_answer(
            question="What is the recovery time objective?",
            context_chunks=sample_chunks,
        )

    assert isinstance(response, QueryResponse)
    assert response.answer == "1 hour"


@pytest.mark.asyncio
async def test_generate_answer_response_validates_against_schema(sample_chunks: list[dict]) -> None:
    """generate_answer output is a valid QueryResponse instance."""
    fake_response = MagicMock()
    fake_response.answer = "1 hour"
    fake_response.confidence = "HIGH"
    fake_response.missing_info = []
    fake_response.citations = [
        Citation(
            chunk_id="chunk-1",
            document_id="doc-1",
            document_name="vertical_slice_fixture.md",
            section="Disaster Recovery",
            excerpt="The recovery time objective is 1 hour.",
            relevance_score=0.95,
        ),
    ]

    with patch("app.services.query_pipeline.ollama_client") as mock_ollama:
        mock_ollama.generate_structured.return_value = fake_response
        response = await generate_answer(
            question="What is the RTO?",
            context_chunks=sample_chunks,
        )

    assert isinstance(response, QueryResponse)
    assert response.is_complete is True
    assert not response.missing_info


@pytest.mark.asyncio
async def test_citations_only_reference_context_chunks(sample_chunks: list[dict]) -> None:
    """Returned citations reference only chunk ids present in the provided context."""
    fake_response = MagicMock()
    fake_response.answer = "1 hour"
    fake_response.confidence = "HIGH"
    fake_response.missing_info = []
    fake_response.citations = [
        Citation(
            chunk_id="chunk-1",
            document_id="doc-1",
            document_name="vertical_slice_fixture.md",
            section="Disaster Recovery",
            excerpt="The recovery time objective is 1 hour.",
            relevance_score=0.95,
        ),
    ]

    with patch("app.services.query_pipeline.ollama_client") as mock_ollama:
        mock_ollama.generate_structured.return_value = fake_response
        response = await generate_answer(
            question="What is the RTO?",
            context_chunks=sample_chunks,
        )

    context_ids = {chunk["id"] for chunk in sample_chunks}
    for citation in response.citations:
        assert citation.chunk_id in context_ids


@pytest.mark.asyncio
async def test_generate_answer_reports_missing_info_for_low_confidence() -> None:
    """When context is insufficient, generate_answer reports missing_info."""
    fake_response = MagicMock()
    fake_response.answer = "I cannot determine the RTO from the provided context."
    fake_response.confidence = "INSUFFICIENT_DATA"
    fake_response.missing_info = ["No Disaster Recovery section found"]
    fake_response.citations = []

    with patch("app.services.query_pipeline.ollama_client") as mock_ollama:
        mock_ollama.generate_structured.return_value = fake_response
        response = await generate_answer(
            question="What is the RTO for MegaCorp?",
            context_chunks=[],
        )

    assert isinstance(response, QueryResponse)
    assert response.confidence.value == "INSUFFICIENT_DATA"
    assert response.is_complete is False
    assert response.missing_info


@pytest.mark.integration
@pytest.mark.asyncio
async def test_integration_query_pipeline_against_fixture() -> None:
    """End-to-end query pipeline against the real compose stack."""
    question = (
        "What is the recovery time objective for Acme Corporation's disaster recovery procedures?"
    )
    query_vector = await generate_query_embedding(question)
    chunks = await retrieve_chunks(query_vector, top_k=3)
    response = await generate_answer(question, context_chunks=chunks)

    assert isinstance(response, QueryResponse)
    assert "1 hour" in response.answer or "60 minutes" in response.answer
    assert response.citations
    for citation in response.citations:
        assert citation.document_name == "vertical_slice_fixture.md"

"""Tests for document processing services."""

from pathlib import Path

import pytest

from app.services.document_processing import chunk_text, extract_text_from_markdown


@pytest.fixture
def fixture_path() -> Path:
    """Path to the vertical-slice fixture markdown file."""
    return Path(__file__).resolve().parents[2] / "eval" / "documents" / "vertical_slice_fixture.md"


def test_extract_text_from_markdown_returns_non_empty_string(fixture_path: Path) -> None:
    """extract_text_from_markdown yields a non-empty string."""
    text = extract_text_from_markdown(fixture_path)
    assert isinstance(text, str)
    assert len(text) > 0
    assert "Acme Corporation" in text


def test_extract_text_from_markdown_preserves_headings(fixture_path: Path) -> None:
    """Headings remain present in extracted Markdown text."""
    text = extract_text_from_markdown(fixture_path)
    assert "## System Architecture" in text
    assert "## Disaster Recovery" in text


def test_chunk_text_produces_list_of_chunks(fixture_path: Path) -> None:
    """chunk_text returns a list of chunk objects."""
    text = extract_text_from_markdown(fixture_path)
    chunks = chunk_text(text, chunk_size=600, overlap=100)
    assert isinstance(chunks, list)
    assert len(chunks) >= 2


def test_chunk_text_chunk_count_for_fixture(fixture_path: Path) -> None:
    """The fixture document produces at least two chunks."""
    text = extract_text_from_markdown(fixture_path)
    chunks = chunk_text(text, chunk_size=600, overlap=100)
    assert len(chunks) >= 2


def test_each_chunk_has_id_text_and_metadata(fixture_path: Path) -> None:
    """Every chunk exposes id, text, and metadata with source and chunk_index."""
    text = extract_text_from_markdown(fixture_path)
    chunks = chunk_text(text, chunk_size=600, overlap=100, source="vertical_slice_fixture.md")

    for index, chunk in enumerate(chunks):
        assert "id" in chunk
        assert "text" in chunk
        assert "metadata" in chunk
        metadata = chunk["metadata"]
        assert metadata["source"] == "vertical_slice_fixture.md"
        assert metadata["chunk_index"] == index


def test_no_chunk_exceeds_token_limit(fixture_path: Path) -> None:
    """No chunk exceeds 800 tokens when chunked with size 600 and overlap 100."""
    text = extract_text_from_markdown(fixture_path)
    chunks = chunk_text(text, chunk_size=600, overlap=100)

    for chunk in chunks:
        token_count = len(chunk["text"].split())
        assert token_count <= 800, f"chunk exceeded 800 tokens: {token_count}"


def test_chunk_text_respects_overlap(fixture_path: Path) -> None:
    """Consecutive chunks share an overlap window."""
    text = extract_text_from_markdown(fixture_path)
    chunks = chunk_text(text, chunk_size=600, overlap=100)
    if len(chunks) >= 2:
        first_words = set(chunks[0]["text"].split()[-50:])
        second_words = set(chunks[1]["text"].split()[:50])
        assert first_words & second_words, "adjacent chunks do not overlap"


def test_chunk_text_preserves_section_headings(fixture_path: Path) -> None:
    """Section headings are carried as metadata where possible."""
    text = extract_text_from_markdown(fixture_path)
    chunks = chunk_text(text, chunk_size=600, overlap=100)

    dr_chunks = [
        chunk
        for chunk in chunks
        if "Disaster Recovery" in chunk["text"]
        or chunk["metadata"].get("section") == "Disaster Recovery"
    ]
    assert dr_chunks, "no chunk covers Disaster Recovery section"

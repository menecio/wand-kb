"""Document text extraction and Markdown-aware chunking."""

import hashlib
import re
from pathlib import Path
from typing import Any


def extract_text_from_markdown(file_path: Path) -> str:
    """Read a Markdown file and return its contents as plain text."""
    return Path(file_path).read_text(encoding="utf-8")


def _split_by_headings(text: str) -> list[tuple[str | None, str]]:
    """Split Markdown text into (heading, section_text) pairs."""
    pattern = re.compile(r"^(#{1,6}\s+.*)$", re.MULTILINE)
    matches = list(pattern.finditer(text))

    if not matches:
        return [(None, text)]

    sections: list[tuple[str | None, str]] = []

    # Text before the first heading.
    first_start = matches[0].start()
    if first_start > 0:
        sections.append((None, text[:first_start].strip()))

    for i, match in enumerate(matches):
        heading = match.group(1).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        section_text = text[start:end].strip()
        sections.append((heading, section_text))

    return sections


def _make_chunk_id(text: str, source: str | None, index: int) -> str:
    """Create a deterministic chunk identifier."""
    content = f"{source or ''}:{index}:{text}"
    return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]


def chunk_text(
    text: str,
    chunk_size: int = 600,
    overlap: int = 100,
    source: str | None = None,
) -> list[dict[str, Any]]:
    """Split text into overlapping chunks, preserving Markdown section headings."""
    sections = _split_by_headings(text)
    chunks: list[dict[str, Any]] = []
    chunk_index = 0

    for heading, section_text in sections:
        if not section_text:
            continue

        section_label = heading.lstrip("#").strip() if heading else None
        prefix = f"{heading}\n\n" if heading else ""
        words = section_text.split()
        available_size = chunk_size - len(prefix.split()) if prefix else chunk_size

        if available_size <= 0:
            available_size = chunk_size

        if len(words) <= available_size and not prefix:
            chunk_text_value = section_text
            chunk_id = _make_chunk_id(chunk_text_value, source, chunk_index)
            chunks.append(
                {
                    "id": chunk_id,
                    "text": chunk_text_value,
                    "metadata": {
                        "source": source,
                        "chunk_index": chunk_index,
                        "section": section_label,
                    },
                }
            )
            chunk_index += 1
            continue

        start = 0
        while start < len(words):
            end = min(start + available_size, len(words))
            chunk_words = words[start:end]
            chunk_text_value = prefix + " ".join(chunk_words) if prefix and start == 0 else " ".join(chunk_words)
            if heading and start > 0 and not chunk_text_value.startswith("#"):
                chunk_text_value = f"{heading}\n\n{chunk_text_value}"

            chunk_id = _make_chunk_id(chunk_text_value, source, chunk_index)
            chunks.append(
                {
                    "id": chunk_id,
                    "text": chunk_text_value,
                    "metadata": {
                        "source": source,
                        "chunk_index": chunk_index,
                        "section": section_label,
                    },
                }
            )
            chunk_index += 1

            if end >= len(words):
                break
            start = end - overlap
            if start < 0:
                start = 0

    return chunks

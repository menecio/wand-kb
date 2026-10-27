"""Test fixtures and binary helpers."""

from __future__ import annotations


def corrupt_pdf_bytes() -> bytes:
    """Bytes that begin like a PDF but are not a valid document."""
    return b"%PDF-1.4\nthis is not a valid pdf object stream\n%%EOF"


def no_text_pdf_bytes() -> bytes:
    """A minimal valid PDF with no extractable text content."""
    return (
        "%PDF-1.4\n"
        "1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        "2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        "3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]>>endobj\n"
        "xref\n"
        "0 4\n"
        "0000000000 65535 f \n"
        "0000000009 00000 n \n"
        "0000000053 00000 n \n"
        "0000000104 00000 n \n"
        "trailer<</Size 4/Root 1 0 R>>\n"
        "startxref\n"
        "166\n"
        "%%EOF\n"
    ).encode("ascii")

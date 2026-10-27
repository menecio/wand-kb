# 0003. PDF parsing: PyMuPDF for text-based PDFs

- Status: Proposed
- Date: 2026-10-27
- Context: Uploaded PDFs must be converted to text for chunking and embedding. Only text-based (digitally authored) PDFs are in scope; image/scanned PDFs are explicitly out of scope. Extraction should be fast and preserve reasonable reading order.
- Decision: Use PyMuPDF (fitz) to extract text from text-based PDFs.
- Alternatives considered:
  - pdfminer.six — rejected because it is slower and more verbose for the same output, with no benefit for text-based documents.
  - pypdf — rejected because its layout/reading-order extraction is weaker and less reliable on multi-column documents.
  - OCR (Tesseract/cloud) — rejected because OCR is explicitly out of scope, adds heavy dependencies and infrastructure, and is not needed for the evaluation dataset.
- Consequences: Fast, high-quality text extraction with layout awareness. Trade-off: scanned/image-only PDFs are unsupported and will yield empty or garbage text; this limitation must be surfaced to users.
# 0006. Supported documents: PDF, Markdown, TXT only; no OCR

- Status: Proposed
- Date: 2026-10-27
- Context: The challenge's evaluation dataset and scope cover PDF, Markdown, and plain text. Supporting additional formats (DOCX, HTML, images) and OCR would require parsers and infrastructure beyond the baseline, risking scope creep in a time-boxed take-home.
- Decision: Support only PDF (text-based), Markdown, and TXT. Reject other formats at upload time. OCR is out of scope.
- Alternatives considered:
  - Broader format support (DOCX/HTML/RTF) — rejected because each adds parser dependencies and edge cases without improving the evaluated RAG quality.
  - OCR for scanned PDFs/images — rejected because it requires Tesseract or cloud OCR services, heavy dependencies, and is explicitly out of scope for the baseline.
  - Auto-conversion via pandoc/LibreOffice — rejected because it adds a system-level dependency and failure modes for marginal coverage.
- Consequences: Clear, testable upload validation and simple ingestion pipeline. Trade-off: users must convert other formats; image-only PDFs will be rejected or yield no text, which must be communicated clearly.
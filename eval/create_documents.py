"""Generate synthetic evaluation documents for the knowledge base RAG pipeline."""

from __future__ import annotations

from pathlib import Path

try:
    import pymupdf as fitz

    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False


ROOT = Path(__file__).parent.resolve()
DOCUMENTS_DIR = ROOT / "documents"

COMPANY_POLICY = """# TechCorp Inc. Company Policy

## Remote Work Policy
TechCorp Inc. supports flexible work arrangements. Employees may work remotely up to 3 days per week, subject to manager approval and team scheduling needs.

## Vacation Policy
All full-time employees receive 20 days of paid vacation per year. Vacation time accrues monthly at a rate of 1.67 days per month and may be carried over up to a maximum of 10 days into the next calendar year.

## Health Insurance
TechCorp Inc. provides comprehensive health insurance that covers the employee and their dependents, including spouse and children under the age of 26.

## Retirement Benefits
The company offers 401k matching up to 4% of salary. Employees are eligible to enroll after 90 days of employment.

## Contact
For questions about policies, contact HR at hr@techcorp.com.
"""

PRODUCT_SPECS = """Product Specifications: SmartWidget Pro

Product Name: SmartWidget Pro
Price: $299.99
Battery Life: 12 hours
Weight: 450 grams
Dimensions: 15cm x 8cm x 2cm
Available Colors: Black, White, Silver
Warranty: 2 years
Release Date: March 15, 2024

The SmartWidget Pro is a premium portable device designed for professionals who need reliable performance on the go.
"""

MEETING_NOTES_TEXT = """Meeting Notes

Meeting Date: January 10, 2024
Attendees: Alice, Bob, Charlie
Topic: Q1 Planning

Summary:
The team met to discuss plans for the first quarter of 2024. Budget approved: $50,000. Project deadline: June 30, 2024.

Action Items:
- Alice leads design
- Bob handles backend
- Charlie manages testing
"""


def write_text_file(path: Path, content: str) -> None:
    """Write a UTF-8 text file."""
    path.write_text(content, encoding="utf-8")


def create_pdf(path: Path, content: str) -> None:
    """Create a simple text-based PDF using PyMuPDF."""
    if not PYMUPDF_AVAILABLE:
        raise RuntimeError("PyMuPDF is not available; cannot create PDF")

    doc = fitz.open()
    page = doc.new_page()
    # Use a text box that occupies most of an A4 page so long lines wrap safely.
    text_rect = fitz.Rect(72, 72, page.rect.width - 72, page.rect.height - 72)
    page.insert_textbox(text_rect, content, fontsize=11)
    doc.save(str(path))
    doc.close()


def main() -> None:
    """Generate all evaluation documents."""
    DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)

    write_text_file(DOCUMENTS_DIR / "company_policy.md", COMPANY_POLICY)
    write_text_file(DOCUMENTS_DIR / "product_specs.txt", PRODUCT_SPECS)

    pdf_path = DOCUMENTS_DIR / "meeting_notes.pdf"
    txt_path = DOCUMENTS_DIR / "meeting_notes.txt"
    if PYMUPDF_AVAILABLE:
        create_pdf(pdf_path, MEETING_NOTES_TEXT)
        # Remove stale fallback file if it exists.
        txt_path.unlink(missing_ok=True)
    else:
        write_text_file(txt_path, MEETING_NOTES_TEXT)
        pdf_path.unlink(missing_ok=True)

    print("Generated evaluation documents:")
    for item in sorted(DOCUMENTS_DIR.iterdir()):
        if item.is_file() and not item.name.startswith("."):
            print(f"  - {item.name}")


if __name__ == "__main__":
    main()

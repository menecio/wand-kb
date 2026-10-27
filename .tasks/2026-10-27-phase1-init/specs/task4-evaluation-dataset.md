# Task 4 Specification: Evaluation Dataset

## Objective
Create synthetic documents and evaluation cases to test the RAG pipeline.

## Deliverables

### 1. Synthetic Documents (3 files)

Create 3 small documents in `eval/documents/`:

#### `eval/documents/company_policy.md` (Markdown)
Content should include:
- Company name: "TechCorp Inc."
- Remote work policy: employees can work remotely up to 3 days per week
- Vacation policy: 20 days per year, accrues monthly
- Health insurance: covers employee + dependents
- 401k matching: up to 4% of salary
- Contact HR: hr@techcorp.com

#### `eval/documents/product_specs.txt` (Plain text)
Content should include:
- Product: "SmartWidget Pro"
- Price: $299.99
- Battery life: 12 hours
- Weight: 450 grams
- Dimensions: 15cm x 8cm x 2cm
- Colors: Black, White, Silver
- Warranty: 2 years
- Release date: March 15, 2024

#### `eval/documents/meeting_notes.pdf` (PDF)
Create a simple text-based PDF with content:
- Meeting date: January 10, 2024
- Attendees: Alice, Bob, Charlie
- Topic: Q1 Planning
- Budget approved: $50,000
- Project deadline: June 30, 2024
- Action items: Alice leads design, Bob handles backend, Charlie manages testing

**Note**: Use a library like `reportlab` or create a minimal valid PDF manually. If PDF generation is too complex, create a `.txt` file instead and document the limitation.

### 2. Evaluation Cases (10 cases)

Create `eval/cases.json` with 10 evaluation cases. Each case must have:

```json
{
  "id": "case_01",
  "question": "...",
  "expected_behavior": "exact_answer | partial_answer | no_answer | clarifying_question",
  "expected_sources": ["company_policy.md", "product_specs.txt", "meeting_notes.pdf"],
  "expected_completeness": "complete | partial | insufficient",
  "notes": "Explanation of what this case tests"
}
```

#### Case Requirements:

**case_01: Direct single-document answer**
- Question: "How many vacation days do employees get?"
- Expected: exact_answer from company_policy.md
- Completeness: complete

**case_02: Direct single-document with specific number**
- Question: "What is the price of SmartWidget Pro?"
- Expected: exact_answer from product_specs.txt
- Completeness: complete

**case_03: Multi-document synthesis**
- Question: "What are the company policies and what products do we sell?"
- Expected: partial_answer combining company_policy.md and product_specs.txt
- Completeness: complete (if both sources referenced)

**case_04: Information not in documents**
- Question: "What is the competitor's pricing strategy?"
- Expected: no_answer
- Completeness: insufficient

**case_05: Ambiguous question**
- Question: "Tell me about the project"
- Expected: clarifying_question (which project? meeting notes or general?)
- Completeness: insufficient

**case_06: Exact identifier lookup**
- Question: "What is the model number for the device with 12-hour battery?"
- Expected: exact_answer (SmartWidget Pro) from product_specs.txt
- Completeness: complete

**case_07: Information at document boundary**
- Question: "Who is responsible for backend development?"
- Expected: exact_answer (Bob) from meeting_notes.pdf
- Completeness: complete

**case_08: Contradictory information (none in current docs)**
- Question: "Are there any conflicts in the documents?"
- Expected: no_answer (no contradictions present)
- Completeness: complete (correctly identifies no conflicts)

**case_09: Date-based query**
- Question: "When is the project deadline?"
- Expected: exact_answer (June 30, 2024) from meeting_notes.pdf
- Completeness: complete

**case_10: Complex multi-facet question**
- Question: "What are the product specifications and who approved the budget?"
- Expected: partial_answer (specs from product_specs.txt, budget from meeting_notes.pdf)
- Completeness: complete (if both aspects addressed)

## Implementation Notes

1. Use PyMuPDF (fitz) to create the PDF:
```python
import fitz

doc = fitz.open()
page = doc.new_page()
page.insert_text((72, 72), "Meeting Notes\n...")
doc.save("eval/documents/meeting_notes.pdf")
```

2. If PyMuPDF is not available, create `meeting_notes.txt` instead and update the expected_sources in evaluation cases accordingly.

3. Ensure all documents are plain text (no images, no complex formatting).

4. Write a Python script `eval/create_documents.py` that generates all documents when run.

## Verification

1. All 3 documents exist in `eval/documents/`
2. `eval/cases.json` contains exactly 10 cases
3. Each case has all required fields
4. Documents are readable and contain the expected information
5. Expected sources in each case match actual document content

Run:
```bash
cd eval
python create_documents.py  # Generate documents
python -c "import json; cases = json.load(open('cases.json')); print(f'{len(cases)} cases loaded')"
```

## Acceptance Criteria

- [ ] 3 documents created (2 text-based, 1 PDF or text alternative)
- [ ] 10 evaluation cases in JSON format
- [ ] Each case has: id, question, expected_behavior, expected_sources, expected_completeness, notes
- [ ] Documents contain all required information
- [ ] Evaluation cases cover all 10 specified scenarios
- [ ] All files are in correct locations

"""Evaluation runner for the Phase 3 RAG core.

Hits the running backend API, records per-case observations, and writes
RESULTS.md. Run from the repo root after `docker compose up -d`.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import requests

BASE_URL = "http://127.0.0.1:8000"
DOCUMENTS_DIR = Path(__file__).parent / "documents"
RESULTS_PATH = Path(__file__).parent / "RESULTS.md"


@dataclass
class CaseResult:
    id: str
    question: str
    expected_behavior: str
    expected_sources: list[str]
    expected_completeness: str
    status_code: int
    response: dict[str, Any] = field(default_factory=dict)
    retrieved_evidence: list[dict[str, Any]] = field(default_factory=list)
    generation_invoked: bool | None = None
    citation_valid: bool | None = None
    confidence: str | None = None
    is_complete: bool | None = None
    missing_info: list[str] = field(default_factory=list)
    suggestions: list[dict[str, Any]] = field(default_factory=list)
    notes: str = ""
    delta: str = ""


def _upload(filename: str, content: bytes) -> str:
    response = requests.post(
        f"{BASE_URL}/api/documents",
        files={"files": (filename, content, "text/plain")},
        timeout=60,
    )
    response.raise_for_status()
    data = response.json()
    result = next(r for r in data["results"] if r["filename"] == filename)
    if result["status"] != "READY":
        raise RuntimeError(f"Upload of {filename} failed: {result}")
    return result["document_id"]


def _search(question: str, top_k: int = 5) -> list[dict[str, Any]]:
    response = requests.post(
        f"{BASE_URL}/api/search",
        json={"query": question, "top_k": top_k},
        timeout=60,
    )
    response.raise_for_status()
    return response.json().get("results", [])


def _query(question: str) -> tuple[int, dict[str, Any]]:
    response = requests.post(
        f"{BASE_URL}/api/query",
        json={"question": question},
        timeout=120,
    )
    try:
        data = response.json()
    except Exception:
        data = {}
    return response.status_code, data


def _citations_valid(response: dict[str, Any], evidence: list[dict[str, Any]]) -> bool:
    citations = response.get("citations", [])
    if not citations:
        return True  # No citations to validate.
    evidence_ids = {c["chunk_id"] for c in evidence}
    return all(c["chunk_id"] in evidence_ids for c in citations)


def _load_case_notes() -> dict[str, str]:
    return {
        "case_01": "Direct single-document answer from company_policy.md.",
        "case_02": "Direct single-document answer from product_specs.txt.",
        "case_03": "Multi-document synthesis combining company_policy.md and product_specs.txt.",
        "case_04": "Irrelevant query; should gate out without generation.",
        "case_05": "Ambiguous question; should ask for clarification.",
        "case_06": "Exact identifier lookup from product_specs.txt.",
        "case_07": "Named responsibility lookup from meeting_notes.pdf.",
        "case_08": "No contradictions in current document set.",
        "case_09": "Date extraction from meeting_notes.pdf.",
        "case_10": "Multi-facet question combining product specs and meeting notes budget approval.",
        "case_11": "Contradictory documents should surface conflict.",
        "case_12": "Prompt injection must not override system instructions.",
        "case_13": "Chunk boundary case: RTO spans chunks.",
        "case_14": "Same filename with different content coexists.",
    }


def _run_case(case: dict[str, Any]) -> CaseResult:
    question = case["question"]
    status_code, response = _query(question)

    # Search for retrieved evidence separately to observe retrieval.
    try:
        evidence = _search(question, top_k=5)
    except Exception as exc:
        evidence = []
        print(f"Search failed for {case['id']}: {exc}", file=sys.stderr)

    confidence = response.get("confidence")
    is_complete = response.get("is_complete")

    # Heuristic: generation was invoked if we see an answer other than the
    # controlled insufficient-data template and confidence is not INSUFFICIENT_DATA.
    answer = response.get("answer", "")
    controlled_phrase = "Sufficient evidence was not retrieved"
    generation_invoked = not (
        confidence == "INSUFFICIENT_DATA" and controlled_phrase in answer
    )

    delta_parts: list[str] = []
    if case["expected_completeness"] == "complete" and not is_complete:
        delta_parts.append("expected complete but got incomplete")
    if case["expected_completeness"] == "insufficient" and is_complete:
        delta_parts.append("expected insufficient but got complete")
    if case["expected_behavior"] == "no_answer" and confidence != "INSUFFICIENT_DATA":
        delta_parts.append("expected no answer but got a factual answer")
    if case["expected_behavior"] == "exact_answer" and confidence == "INSUFFICIENT_DATA":
        delta_parts.append("expected exact answer but gated out")

    return CaseResult(
        id=case["id"],
        question=question,
        expected_behavior=case["expected_behavior"],
        expected_sources=case.get("expected_sources", []),
        expected_completeness=case["expected_completeness"],
        status_code=status_code,
        response=response,
        retrieved_evidence=evidence,
        generation_invoked=generation_invoked,
        citation_valid=_citations_valid(response, evidence) if status_code == 200 else None,
        confidence=confidence,
        is_complete=is_complete,
        missing_info=response.get("missing_info", []),
        suggestions=response.get("enrichment_suggestions", []),
        notes=case.get("notes", ""),
        delta="; ".join(delta_parts) or "matches expected",
    )


def _write_results(results: list[CaseResult]) -> None:
    lines: list[str] = [
        "# Phase 3 Evaluation Results",
        "",
        f"API base URL: {BASE_URL}",
        f"Total cases: {len(results)}",
        "",
        "## Summary",
        "",
        "| Case | Question | Expected | Confidence | Complete | Citation Valid | Generation Invoked | Delta |",
        "|------|----------|----------|------------|----------|----------------|--------------------|-------|",
    ]
    for r in results:
        lines.append(
            f"| {r.id} | {r.question[:60]}{'...' if len(r.question) > 60 else ''} | "
            f"{r.expected_behavior} | {r.confidence or 'N/A'} | {r.is_complete if r.is_complete is not None else 'N/A'} | "
            f"{r.citation_valid if r.citation_valid is not None else 'N/A'} | "
            f"{r.generation_invoked if r.generation_invoked is not None else 'N/A'} | {r.delta} |"
        )

    lines.extend(["", "## Per-case details", ""])
    for r in results:
        lines.extend(
            [
                f"### {r.id}: {r.question}",
                "",
                f"- Expected behavior: {r.expected_behavior}",
                f"- Expected completeness: {r.expected_completeness}",
                f"- Status code: {r.status_code}",
                f"- Confidence: {r.confidence}",
                f"- is_complete: {r.is_complete}",
                f"- Generation invoked (heuristic): {r.generation_invoked}",
                f"- Citation valid: {r.citation_valid}",
                f"- Delta: {r.delta}",
                "",
                "**Retrieved evidence:**",
                "",
                "```json",
                json.dumps(r.retrieved_evidence, indent=2),
                "```",
                "",
                "**Response:**",
                "",
                "```json",
                json.dumps(r.response, indent=2),
                "```",
                "",
            ]
        )

    RESULTS_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote results to {RESULTS_PATH}")


def main() -> None:
    cases_path = Path(__file__).parent / "cases.json"
    cases = json.loads(cases_path.read_text(encoding="utf-8"))

    # Upload all eval documents.
    for path in sorted(DOCUMENTS_DIR.glob("*")):
        if path.is_file() and not path.name.startswith("."):
            print(f"Uploading {path.name}...")
            _upload(path.name, path.read_bytes())

    results: list[CaseResult] = []
    for case in cases:
        print(f"Running {case['id']}...")
        results.append(_run_case(case))

    _write_results(results)


if __name__ == "__main__":
    main()

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, model_validator


class FacetStatus(StrEnum):
    """Status of a question facet."""

    ANSWERED = "ANSWERED"
    PARTIAL = "PARTIAL"
    MISSING = "MISSING"
    UNCERTAIN = "UNCERTAIN"
    CONFLICTING = "CONFLICTING"


class Facet(BaseModel):
    """Internal representation of a question facet for LLM output."""

    description: str
    status: FacetStatus
    citation_ids: list[str]
    associated_gap: str | None = None

    @model_validator(mode="after")
    def check_answered_has_evidence(self) -> Facet:
        # IR-2: Answered facets require evidence
        if self.status == FacetStatus.ANSWERED and not self.citation_ids:
            raise ValueError("ANSWERED facets must have at least one citation_id")
        return self

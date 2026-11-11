"""Data contracts passed between Integration, Input Evaluation (IE) and Claim Investigation (CI).

INT-9: no model has a reporter/author/user field. Do not add one.
"""
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class RawReport(BaseModel):
    """INT-1/INT-2: the original report, kept verbatim. No reporter identity (INT-9)."""
    report_id: str
    original_text: str
    sha256: str
    received_at: datetime
    source: Literal["upload", "paste"]
    repo_url: Optional[str] = None


class StructuredReport(BaseModel):
    """INT-2: every non-null string/list item is an exact substring of the original text."""
    report_id: str
    title: Optional[str] = None
    description: Optional[str] = None
    steps_to_reproduce: Optional[str] = None
    expected_behavior: Optional[str] = None
    observed_behavior: Optional[str] = None
    environment: Optional[str] = None
    code_references: list[str] = Field(default_factory=list)
    versions: list[str] = Field(default_factory=list)


class Evidence(BaseModel):
    """R3/INT-8: where a finding's support comes from. Passed through unchanged."""
    kind: Literal["report_excerpt", "file", "url", "note"]
    ref: str
    excerpt: Optional[str] = None


class Finding(BaseModel):
    """One statement the system makes about a report (INT-5, INT-7)."""
    finding_id: str
    report_id: str
    source: Literal["input_evaluation", "claim_investigation"]
    subject: str  # criterion name (IE) or claim_id (CI)
    status: Literal["satisfied", "not_satisfied", "verified", "refuted", "could_not_check"]
    statement: str
    evidence: list[Evidence] = Field(default_factory=list)


class InvestigationRequest(BaseModel):
    """INT-4: a claim for CI to check, plus the report context it needs."""
    claim_id: str
    report_id: str
    claim_text: str
    context: dict = Field(default_factory=dict)  # repo_url, versions, environment, code_references


class IEResult(BaseModel):
    report_id: str
    findings: list[Finding] = Field(default_factory=list)
    investigation_requests: list[InvestigationRequest] = Field(default_factory=list)


class CIResult(BaseModel):
    report_id: str
    findings: list[Finding] = Field(default_factory=list)


class MaintainerOutput(BaseModel):
    """INT-6/R2: what the maintainer sees. could_not_check is always present (R4)."""
    report_id: str
    sha256: str
    summary: dict[str, int]
    findings: list[Finding]
    could_not_check: list[str]

"""Data contracts passed between Integration, Input Evaluation (IE) and Claim Investigation (CI).

INT-9: no model has a reporter/author/user field. Do not add one.
"""
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class RawReport(BaseModel):
    """INT-1/INT-2: the original report, kept verbatim. No reporter identity (INT-9)."""
    report_id: str
    original_title: Optional[str] = None
    original_body: str
    sha256: str  # of original_title (or "") + "\n" + original_body
    received_at: datetime
    source: Literal["paste", "upload", "github"]
    repo_url: Optional[str] = None
    issue_url: Optional[str] = None


class Section(BaseModel):
    """A piece of the body. Invariant (INT-2): original_body[start:end] == text."""
    label: Optional[str] = None  # heading text as written in the report; None = no heading
    text: str
    start: int
    end: int


class Ref(BaseModel):
    """A code reference or version found in the body. original_body[start:end] == text."""
    text: str
    start: int
    end: int


class StructuredReport(BaseModel):
    """INT-2: everything is an exact slice of the original. Nothing is added or dropped."""
    report_id: str
    title: Optional[str] = None
    fields: dict[str, list[Section]] = Field(default_factory=dict)  # description/steps/expected/observed/environment
    unmapped: list[Section] = Field(default_factory=list)  # preamble and unknown headings
    code_references: list[Ref] = Field(default_factory=list)
    versions: list[Ref] = Field(default_factory=list)


class Evidence(BaseModel):
    """R3/INT-8: where a finding's support comes from. Passed through unchanged."""
    kind: Literal["report_excerpt", "file", "url", "note"]
    ref: str
    excerpt: Optional[str] = None
    start: Optional[int] = None  # span in original_body, for report_excerpt
    end: Optional[int] = None
    line_start: Optional[int] = None  # 1-based lines of that span
    line_end: Optional[int] = None


class Finding(BaseModel):
    """One statement the system makes about a report (INT-5, INT-7)."""
    finding_id: str
    report_id: str
    source: Literal["input_evaluation", "claim_investigation"]
    subject: str  # criterion (IE) or claim_id (CI)
    # IE criteria: present / not_found / unable_to_judge.  CI claims: verified / refuted / could_not_check.
    status: Literal["present", "not_found", "unable_to_judge", "verified", "refuted", "could_not_check"]
    statement: str
    evidence: list[Evidence] = Field(default_factory=list)


class InvestigationRequest(BaseModel):
    """INT-4: a claim for CI to check, plus the report context it needs."""
    claim_id: str
    report_id: str
    claim_text: str
    location: Optional[dict] = None  # {"start": int, "end": int} in original_body (IF05)
    context: dict = Field(default_factory=dict)  # set by Integration
    ie_context: dict = Field(default_factory=dict)  # IE's own context, passed through untouched


Decision = Literal["investigate", "request_more_information", "do_not_investigate"]


class IEResult(BaseModel):
    report_id: str
    decision: Decision = "do_not_investigate"
    reason: str = ""
    missing_information: list[str] = Field(default_factory=list)
    findings: list[Finding] = Field(default_factory=list)
    investigation_requests: list[InvestigationRequest] = Field(default_factory=list)
    not_checked: list[str] = Field(default_factory=list)


class CIResult(BaseModel):
    report_id: str
    findings: list[Finding] = Field(default_factory=list)
    not_checked: list[str] = Field(default_factory=list)  # limits, with reasons (IF08)


class MaintainerOutput(BaseModel):
    """INT-6/R2: what the maintainer sees. could_not_check is always present (R4)."""
    report_id: str
    sha256: str
    source: str
    issue_url: Optional[str] = None
    ie_decision: Decision
    ie_reason: str
    missing_information: list[str]
    findings: list[Finding]
    could_not_check: list[str]
    original_title: Optional[str] = None
    original_body: str
    structured: StructuredReport  # so the evidence can be inspected (R3)

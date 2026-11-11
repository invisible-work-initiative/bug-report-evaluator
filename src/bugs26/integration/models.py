"""Data contracts passed between Integration, Input Evaluation (IE) and Claim Investigation (CI).

Three owners, three groups of classes:
  * Integration-owned: RawReport, StructuredReport, CIRequest, MaintainerOutput.
  * IE-owned (IE* classes): the IE team's draft v1, "Interface agreement: Input Evaluation and Integration"
    (origin/Input-evaluation, documentation/Interface Agreemtn/input-evaluation-integration.md). Field names and values
    are copied from it. Unknown fields are rejected, as that draft requires (section 4.3).
  * CI-owned (CI* classes): the CI team's draft 0.2 (origin/claim-investigation,
    documentation/claim_investigation_interface_agreement.md). Its field names and outcome values are still open;
    the spelling here is provisional.
Integration passes the IE and CI objects through unchanged (INT-8).

INT-9: no model has a reporter/author/user field. Do not add one.
"""
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


# --- IE-owned: report record, Integration -> IE (IE draft v1, section 4.1) ----------------------

Concept = Literal["bug_description", "steps_to_reproduce", "expected_behavior", "observed_behavior",
                  "environment_version", "supporting_evidence"]


class IELines(Strict):
    """Lines of raw_body, numbered from 1 by splitting on line feeds (a CRLF is one break)."""
    start: int
    end: int


class IESection(Strict):
    section_id: str
    field_id: Optional[str] = None  # only when the issue template is known (it is not yet)
    original_label: str  # exact heading, never empty
    required: Optional[bool] = None  # only when the issue template is known
    status: Literal["provided", "blank", "absent"]  # "absent" needs a known template; Integration never sends it
    value: Optional[str] = None  # exact text under the heading, without the heading line
    recognition: Literal["recognized", "unrecognized"]
    semantic_concept: Optional[Concept] = None
    source_lines: Optional[IELines] = None  # heading and value


class IEExtractionDiagnostic(Strict):
    code: str
    message: str


class IEDiagnostic(Strict):
    severity: Literal["warning", "error"]
    code: str
    path: Optional[str] = None  # JSON Pointer
    message: str


class IEExtraction(Strict):
    mode: Literal["structured", "free_form", "unsupported_template", "parse_error"]
    template_id: Optional[str] = None
    diagnostics: list[IEExtractionDiagnostic] = Field(default_factory=list)


class IEReportRecord(Strict):
    """One report per evaluation attempt. Built by Integration from RawReport + StructuredReport.
    repository/issue_number/issue_url/created_at/updated_at are None for pasted or uploaded reports
    (pending IE open question Q3: the draft requires them)."""
    schema_version: Literal["1.0"] = "1.0"
    request_id: str
    snapshot_id: str
    repository: Optional[str] = None  # "owner/project"
    issue_number: Optional[int] = None
    issue_url: Optional[str] = None
    title: str = ""
    raw_body: str = ""
    body_source: Literal["initial", "current"] = "current"
    labels: list[str] = Field(default_factory=list)
    created_at: Optional[str] = None  # RFC 3339
    updated_at: Optional[str] = None
    sections: list[IESection] = Field(default_factory=list)
    extraction: IEExtraction


# --- IE-owned: evaluation result, IE -> Integration (IE draft v1, section 4.2) -------------------

class IEEvidence(Strict):
    basis: Literal["quotation", "absence_check", "source_reference"]
    source: Literal["title", "raw_body", "whole_report"]
    section_id: Optional[str] = None
    lines: Optional[IELines] = None
    quote: Optional[str] = None
    explanation: str


class IEUnevaluatedReason(Strict):
    code: Literal["unsupported_content", "unsupported_language", "dependency_unavailable", "internal_error"]
    message: str


class IEFinding(Strict):
    criterion_id: Literal["C1", "C2", "C3", "C4", "C5", "C6", "C7"]
    criteria_version: Optional[str] = None
    evaluation_status: Literal["concluded", "unevaluated"]
    rating: Optional[Literal["P", "M", "N/A", "U"]] = None  # None when unevaluated
    explanation: str
    evidence: list[IEEvidence]
    unevaluated_reason: Optional[IEUnevaluatedReason] = None


class IEClaim(Strict):
    claim_id: str  # unique within the response; the full key is (request_id, claim_id)
    claim_text: str
    source: IEEvidence  # a quotation whose quote equals claim_text
    named_project_versions: list[str] = Field(default_factory=list)
    relevant_context: str


class IEClaimExtraction(Strict):
    status: Literal["completed", "partial", "not_performed"]
    reason: Optional[str] = None


class IEProvenance(Strict):
    criteria_version: Optional[str] = None
    evaluator_version: str
    external_models: list[dict] = Field(default_factory=list)  # {"provider", "model", "version"}
    evaluated_at: str


class IEResult(Strict):
    schema_version: Literal["1.0"] = "1.0"
    request_id: Optional[str]
    snapshot_id: Optional[str]
    processing_status: Literal["completed", "partial", "invalid_input", "failed"]
    criterion_findings: list[IEFinding] = Field(default_factory=list)
    unevaluated_criteria: list[str] = Field(default_factory=list)
    claim_extraction: IEClaimExtraction
    identified_claims: list[IEClaim] = Field(default_factory=list)
    no_checkable_claims: Optional[bool] = None
    diagnostics: list[IEDiagnostic] = Field(default_factory=list)
    provenance: IEProvenance


# --- Integration-owned: the original report and its structure (INT-1, INT-2) ---------------------

class RawReport(BaseModel):
    """INT-1/INT-2: the original report, kept verbatim. No reporter identity (INT-9).
    report_id is Integration's own link key (INT-7); request_id/snapshot_id are the IE draft's keys."""
    report_id: str
    request_id: str
    snapshot_id: str
    sha256: str  # of title + "\n" + raw_body
    received_at: datetime
    source: Literal["paste", "upload", "github"]
    repository: Optional[str] = None
    issue_number: Optional[int] = None
    issue_url: Optional[str] = None
    title: str = ""
    raw_body: str
    body_source: Literal["initial", "current"] = "current"  # always "current": the initial text is not available
    labels: list[str] = Field(default_factory=list)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class StructuredReport(BaseModel):
    """INT-2: sections as IE wants them. Nothing is added or dropped; every value is an exact slice of raw_body.
    spans (Integration-private, not sent to IE) holds each value's character offsets for verify_structured."""
    report_id: str
    title: str = ""
    sections: list[IESection] = Field(default_factory=list)
    extraction: IEExtraction
    spans: dict[str, tuple[int, int]] = Field(default_factory=dict)


# --- CI-owned (CI draft 0.2): proposed request, Integration -> CI; result, CI -> Integration -----

class CIRequest(Strict):
    """PROPOSED, not in the CI agreement (CIA covers CI -> Integration only). Built by Integration (INT-4):
    claim_id, claim_text, relevant_context, named_project_versions come from IE untouched; the rest is report context."""
    request_id: str
    claim_id: str
    claim_text: str
    relevant_context: str
    named_project_versions: list[str] = Field(default_factory=list)
    repository: Optional[str] = None
    issue_url: Optional[str] = None
    title: str = ""
    raw_body: str = ""


class CIEvidence(Strict):
    type: str  # e.g. source code, file path, documentation, commit, issue, repository URL
    reference: str  # path or URL, passed on unchanged (INT-8)
    explanation: str


class CIFinding(Strict):
    claim_id: str
    outcome: Literal["supported", "contradicted", "insufficient evidence"]  # provisional spelling
    explanation: str
    evidence: list[CIEvidence] = Field(default_factory=list)  # may be empty for insufficient evidence


class CIResult(Strict):
    """Exactly one finding per claim is expected; Integration reports zero or several as a failure."""
    request_id: str
    claim_id: str
    findings: list[CIFinding] = Field(default_factory=list)
    limitation: Optional[str] = None  # why the claim could not be fully checked


# --- Integration-owned: what the maintainer sees (INT-6) ----------------------------------------

class MaintainerOutput(BaseModel):
    """ie and ci_results are passed through verbatim (INT-8). could_not_check is always present (R4)."""
    report_id: str
    request_id: str
    snapshot_id: str
    sha256: str
    source: str
    issue_url: Optional[str] = None
    title: str = ""
    raw_body: str
    ie: IEResult
    ci_results: list[CIResult]
    could_not_check: list[str]
    structured: StructuredReport  # so the sections can be inspected (R3)

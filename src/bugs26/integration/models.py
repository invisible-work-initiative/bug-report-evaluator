"""Data contracts passed between Integration, Input Evaluation (IE) and Claim Investigation (CI).

Integration-owned: RawReport, StructuredReport, CIRequest, MaintainerOutput.
IE-owned (IE*): IE draft v1 (Input-evaluation branch, "Interface Agreemtn/input-evaluation-integration.md"); names and
values are copied, every field is required, unknown fields are rejected (its section 4.3).
CI-owned (CI*): CI draft 0.2 (claim-investigation branch); its schema is open, so extra fields are accepted.
Integration passes IE and CI objects through unchanged (INT-8).

INT-9: no model has a reporter/author/user field. Do not add one.
"""
from datetime import datetime
from typing import Annotated, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, PositiveInt


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


# --- IE-owned: report record, Integration -> IE (IE draft v1, section 4.1) ----------------------
Concept = Literal["bug_description", "steps_to_reproduce", "expected_behavior", "observed_behavior",
                  "environment_version", "supporting_evidence"]
Id = Annotated[str, Field(min_length=1)]
CriterionId = Literal["C1", "C2", "C3", "C4", "C5", "C6", "C7"]
CRITERIA = {"C1": "Bug description", "C2": "Steps to reproduce", "C3": "Expected behavior", "C4": "Observed behavior",
            "C5": "Environment and version", "C6": "Supporting evidence", "C7": "Clarity and specificity"}  # quality criteria doc


class IELines(Strict):
    """Lines of raw_body, numbered from 1 by splitting on line feeds (a CRLF is one break)."""
    start: PositiveInt
    end: PositiveInt


class IESection(Strict):
    section_id: Id
    field_id: Optional[str]  # only when the issue template is known (it is not yet)
    original_label: Id  # exact heading
    required: Optional[bool]  # only when the issue template is known
    status: Literal["provided", "blank", "absent"]  # "absent" needs a known template; Integration never sends it
    value: Optional[str]  # exact text under the heading, without the heading line
    recognition: Literal["recognized", "unrecognized"]
    semantic_concept: Optional[Concept]
    source_lines: Optional[IELines]  # heading and value


class IEExtractionDiagnostic(Strict):
    code: Id
    message: Id


class IEDiagnostic(Strict):
    severity: Literal["warning", "error"]
    code: Id
    path: Optional[str]  # JSON Pointer
    message: Id


class IEExtraction(Strict):
    mode: Literal["structured", "free_form", "unsupported_template", "parse_error"]
    template_id: Optional[str]
    diagnostics: list[IEExtractionDiagnostic]  # non-empty for unsupported_template and parse_error


class IEReportRecord(Strict):
    """One report per evaluation attempt (the snapshot). The GitHub fields are None for pasted or uploaded reports
    (pending IE question Q3: the draft requires them)."""
    schema_version: Literal["1.0"]
    request_id: Id
    snapshot_id: Id
    repository: Optional[str]  # "owner/project"
    issue_number: Optional[PositiveInt]
    issue_url: Optional[str]
    title: str
    raw_body: str
    body_source: Literal["initial", "current"]
    labels: list[str]
    created_at: Optional[str]  # RFC 3339
    updated_at: Optional[str]
    sections: list[IESection]
    extraction: IEExtraction


class IEEvidence(Strict):
    basis: Literal["quotation", "absence_check", "source_reference"]
    source: Literal["title", "raw_body", "whole_report"]
    section_id: Optional[str]
    lines: Optional[IELines]
    quote: Optional[str]
    explanation: Id


class IEUnevaluatedReason(Strict):
    code: Literal["unsupported_content", "unsupported_language", "dependency_unavailable", "internal_error"]
    message: Id


class IEFinding(Strict):
    criterion_id: CriterionId
    criteria_version: Id
    evaluation_status: Literal["concluded", "unevaluated"]
    rating: Optional[Literal["P", "M", "N/A", "U"]]  # None when unevaluated
    explanation: Id
    evidence: Annotated[list[IEEvidence], Field(min_length=1)]
    unevaluated_reason: Optional[IEUnevaluatedReason]


class IEClaim(Strict):
    claim_id: Id  # unique within the response; the full key is (request_id, claim_id)
    claim_text: Id
    source: IEEvidence  # a quotation whose quote equals claim_text
    named_project_versions: list[str]
    relevant_context: Id


class IEClaimExtraction(Strict):
    status: Literal["completed", "partial", "not_performed"]
    reason: Optional[str]


class IEExternalModel(Strict):
    provider: str
    model: str
    version: str


class IEProvenance(Strict):
    criteria_version: Optional[str]
    evaluator_version: Id
    external_models: list[IEExternalModel]
    evaluated_at: Id


class IEResult(Strict):
    schema_version: Literal["1.0"]
    request_id: Optional[str]
    snapshot_id: Optional[str]
    processing_status: Literal["completed", "partial", "invalid_input", "failed"]
    criterion_findings: list[IEFinding]
    unevaluated_criteria: list[CriterionId]
    claim_extraction: IEClaimExtraction
    identified_claims: list[IEClaim]
    no_checkable_claims: Optional[bool]
    diagnostics: list[IEDiagnostic]
    provenance: IEProvenance


# --- Integration-owned: the original report and its structure (INT-1, INT-2) ---------------------

class RawReport(BaseModel):
    """INT-1/INT-2: the original report, verbatim. No reporter identity (INT-9). request_id is the INT-7 link key."""
    request_id: str
    snapshot_id: str
    sha256: str  # of title + newline + raw_body
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
    """INT-2: IE sections; every value is an exact slice of raw_body. spans (private, never serialised) = char offsets."""
    sections: list[IESection]
    extraction: IEExtraction
    spans: dict[str, tuple[int, int]] = Field(default_factory=dict, exclude=True)


class CIModel(BaseModel):
    model_config = ConfigDict(extra="allow")


class CIRequest(Strict):
    """PROPOSED, not in the CI agreement. The claim parts come from IE untouched; the rest is report context (INT-4)."""
    request_id: str
    snapshot_id: str
    claim_id: str
    claim_text: str
    source: IEEvidence
    relevant_context: str
    named_project_versions: list[str]
    repository: Optional[str]
    issue_url: Optional[str]
    title: str
    raw_body: str


class CIEvidence(CIModel):
    type: str  # e.g. source code, file path, documentation, commit, issue, repository URL
    reference: str  # path or URL, passed on unchanged (INT-8)
    explanation: str


class CIFinding(CIModel):
    claim_id: str
    outcome: Literal["supported", "contradicted", "insufficient evidence"]  # provisional spelling
    explanation: str
    evidence: list[CIEvidence] = Field(default_factory=list)  # may be empty for insufficient evidence


class CIResult(CIModel):
    """Exactly one finding per claim; zero or several is a failure. request_id is Integration's ask (CI draft: claim_id only)."""
    request_id: str
    claim_id: str
    findings: list[CIFinding] = Field(default_factory=list)
    limitation: Optional[str] = None  # why the claim could not be fully checked


class MaintainerOutput(BaseModel):
    """record (the snapshot, IE 4.3), ie and ci_results are passed through verbatim (INT-8). could_not_check is always
    present (R4). placeholders names the subsystems that are stubs."""
    sha256: str
    source: str
    placeholders: list[str] = Field(default_factory=list)
    record: IEReportRecord
    ie: IEResult
    ci_results: list[CIResult]
    could_not_check: list[str]

"""INT-4: send investigation requests, with report context, to Claim Investigation."""
from typing import Protocol

from .intake import meaningful_text
from .models import CIResult, IEResult, InvestigationRequest, RawReport, StructuredReport


class ClaimInvestigator(Protocol):
    """Interface Claim Investigation implements. Real CI code replaces the stub."""
    def investigate(self, request: InvestigationRequest) -> CIResult: ...


def to_investigation(raw: RawReport, structured: StructuredReport,
                     ie: IEResult, investigator: ClaimInvestigator) -> CIResult:
    """INT-4 + routing rule (BRE-DR.11): call CI only if IE decided "investigate" AND sent >= 1 request.
    Otherwise CI is skipped and the reason goes into not_checked (shown as "could not check")."""
    for request in ie.investigation_requests:
        if request.report_id != raw.report_id:
            raise ValueError(f"request {request.claim_id} belongs to another report")
    if ie.decision != "investigate":
        return CIResult(report_id=raw.report_id, not_checked=[f"Claims not investigated: {ie.reason}"])
    if not ie.investigation_requests:
        return CIResult(report_id=raw.report_id, not_checked=["No specific bug claim was identified"])

    context = {
        "repo_url": raw.repo_url,
        "issue_url": raw.issue_url,
        "versions": [v.text for v in structured.versions],
        "environment": [meaningful_text(s) for s in structured.fields.get("environment", []) if meaningful_text(s)],
        "code_references": [r.text for r in structured.code_references],
    }
    result = CIResult(report_id=raw.report_id)
    for request in ie.investigation_requests:
        request = request.model_copy(update={"context": context})  # ie_context stays as IE sent it
        answer = investigator.investigate(request)
        result.findings.extend(answer.findings)
        result.not_checked.extend(n for n in answer.not_checked if n not in result.not_checked)
    return result

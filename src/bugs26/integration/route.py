"""INT-4: send investigation requests, with report context, to Claim Investigation."""
from typing import Protocol

from .models import CIResult, IEResult, InvestigationRequest, RawReport, StructuredReport


class ClaimInvestigator(Protocol):
    """Interface Claim Investigation implements. Real CI code replaces the stub."""
    def investigate(self, request: InvestigationRequest) -> CIResult: ...


def to_investigation(raw: RawReport, structured: StructuredReport,
                     ie: IEResult, investigator: ClaimInvestigator) -> CIResult:
    """INT-4: attach the report context to each request and hand it to CI."""
    context = {
        "repo_url": raw.repo_url,
        "versions": structured.versions,
        "environment": structured.environment,
        "code_references": structured.code_references,
    }
    findings = []
    for request in ie.investigation_requests:
        request = request.model_copy(update={"context": context})
        findings.extend(investigator.investigate(request).findings)
    return CIResult(report_id=raw.report_id, findings=findings)

"""INT-4: send investigation requests, with report context, to Claim Investigation."""
from .interfaces import ClaimInvestigator
from .intake import meaningful_text
from .models import CIResult, IEResult, RawReport, StructuredReport


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

    context = {"repo_url": raw.repo_url, "issue_url": raw.issue_url,
               "fields": {name: [meaningful_text(s) for s in sections if meaningful_text(s)]
                          for name, sections in structured.fields.items()}}
    result = CIResult(report_id=raw.report_id)
    for request in ie.investigation_requests:
        request = request.model_copy(update={"context": context})  # ie_context stays as IE sent it
        try:
            answer = investigator.investigate(request)
            if answer.report_id != request.report_id:
                raise ValueError("its answer belongs to another report")
        except Exception as e:  # CI failing must not hide IE's findings (R4): report it and go on
            result.not_checked.append(f"Claim Investigation failed: {type(e).__name__}: {str(e)[:200]}")
            continue
        result.findings.extend(answer.findings)
        result.not_checked.extend(n for n in answer.not_checked if n not in result.not_checked)
    return result

"""INT-4: send one investigation request per identified claim, with report context, to Claim Investigation."""
from .intake import InputEvaluationError
from .interfaces import ClaimInvestigator
from .models import CIRequest, CIResult, IEResult, RawReport

CRITERIA = ["C1", "C2", "C3", "C4", "C5", "C6", "C7"]


def match_ie(raw: RawReport, ie: IEResult) -> None:
    """IE draft 4.3: match the result to its request by request_id + snapshot_id; an invalid result is a failure."""
    if ie.processing_status == "invalid_input" and ie.request_id is None:
        return  # IE could not read the ids; matched by the call itself
    if (ie.request_id, ie.snapshot_id) != (raw.request_id, raw.snapshot_id):
        raise InputEvaluationError("Input Evaluation answered for another request (request_id/snapshot_id differ).")
    if ie.processing_status in ("completed", "partial") and sorted(f.criterion_id for f in ie.criterion_findings) != CRITERIA:
        raise InputEvaluationError("Input Evaluation result does not have exactly one finding for each of C1-C7.")
    claim_ids = [c.claim_id for c in ie.identified_claims]
    if len(set(claim_ids)) != len(claim_ids):
        raise InputEvaluationError("Input Evaluation result repeats a claim_id.")


def to_investigation(raw: RawReport, ie: IEResult, investigator: ClaimInvestigator) -> tuple[list[CIResult], list[str]]:
    """Mechanical routing (IE draft: Integration forwards every claim it receives): one CI call per claim.
    Skipped, with a stated reason, if IE failed or rejected the input, claim extraction was not performed,
    or there are no checkable claims. Returns (CI results, Integration-level notes for could_not_check)."""
    if ie.processing_status in ("invalid_input", "failed"):
        return [], [f"Claims not investigated: Input Evaluation returned {ie.processing_status}."]
    if ie.claim_extraction.status == "not_performed":
        return [], [f"Claims not investigated: claim extraction was not performed ({ie.claim_extraction.reason})."]
    if ie.no_checkable_claims:
        return [], ["No checkable claim was identified, so Claim Investigation was not called."]
    results, notes = [], []
    for claim in ie.identified_claims:
        request = CIRequest(request_id=raw.request_id, claim_id=claim.claim_id, claim_text=claim.claim_text,
                            relevant_context=claim.relevant_context,
                            named_project_versions=claim.named_project_versions,
                            repository=raw.repository, issue_url=raw.issue_url, title=raw.title, raw_body=raw.raw_body)
        try:
            answer = investigator.investigate(request)
        except Exception as e:  # CI failing must not hide IE's findings (R4): report it and go on
            notes.append(f"Claim Investigation failed for claim '{claim.claim_text}': {type(e).__name__}: {str(e)[:200]}")
            continue
        if (answer.request_id, answer.claim_id) != (request.request_id, request.claim_id):
            notes.append(f"Claim Investigation answered for another claim; nothing recorded for '{claim.claim_text}'.")
        elif len(answer.findings) != 1 or answer.findings[0].claim_id != claim.claim_id:
            notes.append(f"Claim Investigation returned {len(answer.findings)} findings for claim "
                         f"'{claim.claim_text}'; exactly one for this claim is required, so none is shown.")
        else:
            results.append(answer)
    return results, notes

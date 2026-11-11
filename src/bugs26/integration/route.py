"""INT-4: send one investigation request per identified claim, with report context, to Claim Investigation."""
from .intake import InputEvaluationError
from .interfaces import ClaimInvestigator
from .models import CRITERIA, CIRequest, CIResult, IEResult, RawReport


def match_ie(raw: RawReport, ie: IEResult) -> None:
    """IE draft 4.3 and 4.2: match the result to its request by request_id + snapshot_id, and check that it is
    consistent with the status table. Any violation is a failure of Input Evaluation, never shown as findings."""
    bad = lambda why: InputEvaluationError(f"Input Evaluation returned an invalid result: {why}.")
    if not (ie.processing_status == "invalid_input" and ie.request_id is None):  # unreadable ids: matched by the call
        if (ie.request_id, ie.snapshot_id) != (raw.request_id, raw.snapshot_id):
            raise bad("it answers another request (request_id/snapshot_id differ)")
    ids = [f.criterion_id for f in ie.criterion_findings]
    unevaluated = [f.criterion_id for f in ie.criterion_findings if f.evaluation_status == "unevaluated"]
    errors = [d for d in ie.diagnostics if d.severity == "error"]
    ext_done = ie.claim_extraction.status == "completed"
    if ie.processing_status in ("completed", "partial"):
        if sorted(ids) != sorted(CRITERIA):
            raise bad("not exactly one finding for each of C1-C7")
    elif ids or ie.identified_claims or not errors:
        raise bad(f"{ie.processing_status} needs no findings, no claims and an error diagnostic")
    if ie.processing_status == "invalid_input" and ie.claim_extraction.status != "not_performed":
        raise bad("invalid_input needs claim_extraction not_performed")
    if ie.processing_status == "completed" and (unevaluated or not ext_done or errors):
        raise bad("completed needs every criterion concluded, claim extraction completed and no error diagnostics")
    if ie.processing_status == "partial" and not ((unevaluated or not ext_done) and errors):
        raise bad("partial needs an unevaluated criterion or incomplete extraction, and an error diagnostic")
    if ie.unevaluated_criteria != unevaluated:
        raise bad("unevaluated_criteria does not list the unevaluated findings")
    for f in ie.criterion_findings:
        if (f.rating is None) != (f.evaluation_status == "unevaluated") or                 (f.unevaluated_reason is None) != (f.evaluation_status == "concluded"):
            raise bad(f"{f.criterion_id} has a rating or unevaluated_reason that does not fit its evaluation_status")
        if f.criteria_version != ie.provenance.criteria_version:
            raise bad(f"{f.criterion_id} criteria_version differs from provenance")
    if len({c.claim_id for c in ie.identified_claims}) != len(ie.identified_claims):
        raise bad("a claim_id is repeated")
    for c in ie.identified_claims:
        if c.source.basis != "quotation" or c.source.quote != c.claim_text:
            raise bad(f"claim {c.claim_id} source is not a quotation of its claim_text")
    if ie.no_checkable_claims != (not ie.identified_claims if ext_done else None):
        raise bad("no_checkable_claims does not fit the claims and claim_extraction status")
    # IF-6: every quotation is found exactly in its source, inside its lines (LF-split lines; a CRLF is one break)
    evidence = [(f"{f.criterion_id} evidence", e) for f in ie.criterion_findings for e in f.evidence]
    evidence += [(f"claim {c.claim_id} source", c.source) for c in ie.identified_claims]
    for where, ev in evidence:
        if ev.basis != "quotation":
            continue
        text = {"title": raw.title, "raw_body": raw.raw_body, "whole_report": raw.title + "\n" + raw.raw_body}[ev.source]
        if ev.lines is not None and ev.source == "raw_body":
            text = "\n".join(raw.raw_body.split("\n")[ev.lines.start - 1:ev.lines.end])
        if not ev.quote or ev.quote not in text:
            raise bad(f"{where}: the quotation is not found in {ev.source}" + (" at its lines" if ev.lines else ""))


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
        request = CIRequest(request_id=raw.request_id, snapshot_id=raw.snapshot_id, claim_id=claim.claim_id,
                            claim_text=claim.claim_text, source=claim.source, relevant_context=claim.relevant_context,
                            named_project_versions=claim.named_project_versions,
                            repository=raw.repository, issue_url=raw.issue_url, title=raw.title, raw_body=raw.raw_body)
        try:
            answer = investigator.investigate(request)
        except Exception as e:  # CI failing must not hide IE's findings (R4): report it and go on
            notes.append(f"Claim '{claim.claim_text}' not investigated: {type(e).__name__}: {str(e)[:200]}")
            continue
        if (answer.request_id, answer.claim_id) != (request.request_id, request.claim_id):
            notes.append(f"Claim Investigation answered for another claim; nothing recorded for '{claim.claim_text}'.")
        elif len(answer.findings) != 1 or answer.findings[0].claim_id != claim.claim_id:
            notes.append(f"Claim Investigation returned {len(answer.findings)} findings for claim "
                         f"'{claim.claim_text}'; exactly one for this claim is required, so none is shown.")
        else:
            results.append(answer)
    return results, notes

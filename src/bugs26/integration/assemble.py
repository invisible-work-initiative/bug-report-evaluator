"""INT-5/6/7/8: build the maintainer output. IE and CI objects are passed through unchanged (INT-8)."""
from .models import CIResult, IEResult, MaintainerOutput, RawReport, StructuredReport


def could_not_check(ie: IEResult, ci_results: list[CIResult], notes: list[str]) -> list[str]:
    """R4: everything that was not or could not be checked. Unrecognized headings are not listed here (IE reads
    the raw text); they are in structured.extraction.diagnostics."""
    out = []
    if ie.processing_status != "completed":
        out.append(f"Input Evaluation status: {ie.processing_status}.")
    for f in ie.criterion_findings:
        if f.evaluation_status == "unevaluated" and f.unevaluated_reason:
            out.append(f"{f.criterion_id} not evaluated ({f.unevaluated_reason.code}): {f.unevaluated_reason.message}")
        elif f.rating == "U":
            out.append(f"{f.criterion_id} rated U (unclear): {f.explanation}")
    if ie.claim_extraction.status != "completed":
        out.append(f"Claim extraction {ie.claim_extraction.status}: {ie.claim_extraction.reason}")
    for d in ie.diagnostics:
        if d.severity == "error" and not any(d.message in line for line in out):
            out.append(f"Input Evaluation error {d.code}: {d.message}")
    text = {c.claim_id: c.claim_text for c in ie.identified_claims}
    for r in ci_results:
        parts = (["insufficient evidence"] if r.findings[0].outcome == "insufficient evidence" else []) + \
                ([r.limitation] if r.limitation else [])
        if parts:
            out.append(f"Claim '{text.get(r.claim_id, r.claim_id)}': " + "; ".join(parts))
    return out + notes or ["Input Evaluation and Claim Investigation reported no limits."]


def build_output(raw: RawReport, structured: StructuredReport, ie: IEResult,
                 ci_results: list[CIResult], notes: list[str]) -> MaintainerOutput:
    """INT-6: combine the results into the maintainer output. INT-7: every result carries this report's request_id."""
    for r in ci_results:
        if r.request_id != raw.request_id:
            raise ValueError(f"CI result for claim {r.claim_id} belongs to another request")
    return MaintainerOutput(
        report_id=raw.report_id, request_id=raw.request_id, snapshot_id=raw.snapshot_id, sha256=raw.sha256,
        source=raw.source, issue_url=raw.issue_url, title=raw.title, raw_body=raw.raw_body,
        ie=ie, ci_results=ci_results, could_not_check=could_not_check(ie, ci_results, notes), structured=structured)

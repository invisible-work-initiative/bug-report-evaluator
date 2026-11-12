"""INT-5/6/7/8: build the maintainer output. The snapshot record and the IE and CI objects are passed through unchanged (INT-8)."""
from .models import CIRequest, CIResult, IEReportRecord, IEResult, MaintainerOutput, RawReport


def could_not_check(ie: IEResult, ci_results: list[CIResult], notes: list[str]) -> list[str]:
    """R4: everything that was not or could not be checked (the processing status itself is shown in the page banner
    and is in ie.processing_status). Unrecognized headings are not gaps: IE reads the raw text."""
    out, reasons = [], set()
    if ie.processing_status in ("invalid_input", "failed"):
        out.append(f"No criterion was evaluated: Input Evaluation returned {ie.processing_status}.")
    for f in ie.criterion_findings:
        if f.evaluation_status == "unevaluated":
            reasons.add(f.unevaluated_reason.message)
            out.append(f"{f.criterion_id} not evaluated ({f.unevaluated_reason.code}): {f.unevaluated_reason.message}")
        elif f.rating == "U":
            out.append(f"{f.criterion_id} rated U (unclear): {f.explanation}")
    if ie.claim_extraction.status != "completed":
        out.append(f"Claim extraction {ie.claim_extraction.status}: {ie.claim_extraction.reason}")
    # an error diagnostic is skipped only if an unevaluated finding above already gave the same message
    out += [f"Input Evaluation error {d.code}: {d.message}" for d in ie.diagnostics
            if d.severity == "error" and d.message not in reasons]
    text = {c.claim_id: c.claim_text for c in ie.identified_claims}
    for r in ci_results:
        parts = (["insufficient evidence"] if r.findings[0].outcome == "insufficient evidence" else []) + \
                ([r.limitation] if r.limitation else [])
        if parts:
            out.append(f"Claim '{text.get(r.claim_id, r.claim_id)}': " + "; ".join(parts))
    return out + notes or ["Input Evaluation and Claim Investigation reported no limits."]


def build_output(raw: RawReport, record: IEReportRecord, ie: IEResult, ci_requests: list[CIRequest],
                 ci_results: list[CIResult], notes: list[str], placeholders: list[str]) -> MaintainerOutput:
    """INT-6: combine the results into the maintainer output (route has checked the request_id of every result).
    record, ie, ci_requests and ci_results are exactly what crossed each interface."""
    return MaintainerOutput(sha256=raw.sha256, source=raw.source, placeholders=placeholders, record=record, ie=ie,
                            ci_requests=ci_requests, ci_results=ci_results,
                            could_not_check=could_not_check(ie, ci_results, notes))

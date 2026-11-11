"""INT-5/6/7/8: collect findings and build the maintainer output."""
from .models import CIResult, Finding, IEResult, MaintainerOutput, RawReport, StructuredReport


def collect(report_id: str, ie: IEResult, ci: CIResult) -> list[Finding]:
    """INT-5 + INT-7: gather findings from both subsystems; findings must belong to this report.
    Findings (and their Evidence) are passed through unchanged (INT-8)."""
    findings = list(ie.findings) + list(ci.findings)
    for f in findings:
        if f.report_id != report_id:
            raise ValueError(f"finding {f.finding_id} belongs to report {f.report_id}, not {report_id}")
    return findings


def parse_gaps(structured: StructuredReport) -> list[str]:
    """What Integration itself could not map (R4)."""
    labels = [s.label for s in structured.unmapped if s.label]
    gaps = ["Sections not mapped: " + ", ".join(labels)] if labels else []
    if gaps and not structured.fields:
        gaps.append("No headings were recognised (non-English or non-standard template?)")
    return gaps


def build_output(raw: RawReport, structured: StructuredReport, ie: IEResult, ci: CIResult,
                 findings: list[Finding]) -> MaintainerOutput:
    """INT-6: combine findings into the maintainer output. could_not_check is always present (R4)."""
    could_not_check = ie.not_checked + ci.not_checked + parse_gaps(structured)
    if not could_not_check:
        could_not_check = ["Input Evaluation and Claim Investigation reported no limits."]
    return MaintainerOutput(
        report_id=raw.report_id,
        sha256=raw.sha256,
        source=raw.source,
        issue_url=raw.issue_url,
        ie_decision=ie.decision,
        ie_reason=ie.reason,
        missing_information=ie.missing_information,
        findings=findings,
        could_not_check=could_not_check,
        original_title=raw.original_title,
        original_body=raw.original_body,
        structured=structured,
    )

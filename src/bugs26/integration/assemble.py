"""INT-5/6/7/8: collect findings and build the maintainer output."""
from collections import Counter

from .models import CIResult, Finding, IEResult, MaintainerOutput

# R4: always stated, whatever else was checked.
FIXED_NOTE = ("NOT CHECKED: Claim Investigation is a placeholder in this prototype, so no claim "
              "in the report was verified against the repository, code or history.")


def collect(report_id: str, ie: IEResult, ci: CIResult) -> list[Finding]:
    """INT-5 + INT-7: gather findings from both subsystems; each must belong to this report.
    Findings (and their Evidence) are passed through unchanged (INT-8)."""
    findings = list(ie.findings) + list(ci.findings)
    for f in findings:
        if f.report_id != report_id:
            raise ValueError(f"finding {f.finding_id} belongs to report {f.report_id}, not {report_id}")
    return findings


def build_output(report_id: str, sha256: str, findings: list[Finding]) -> MaintainerOutput:
    """INT-6: combine findings into the maintainer output. could_not_check is always present (R4)."""
    not_checked = [f"{f.subject}: {f.statement}" for f in findings if f.status == "could_not_check"]
    return MaintainerOutput(
        report_id=report_id,
        sha256=sha256,
        summary=dict(Counter(f.status for f in findings)),
        findings=findings,
        could_not_check=not_checked + [FIXED_NOTE],
    )

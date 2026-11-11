"""PLACEHOLDER Input Evaluation. The real IE subsystem (another team) replaces this.

It only checks whether each section exists. It does not judge quality.
"""
from ..integration.models import Evidence, Finding, IEResult, InvestigationRequest, RawReport, StructuredReport

PLACEHOLDER = "[PLACEHOLDER Input Evaluation] "
CRITERIA = [
    ("title", "title"),
    ("steps_to_reproduce", "steps to reproduce"),
    ("expected_behavior", "expected behavior"),
    ("observed_behavior", "observed behavior"),
    ("environment", "environment"),
]


class StubInputEvaluator:
    def evaluate(self, raw: RawReport, structured: StructuredReport) -> IEResult:
        findings = []
        for n, (attr, name) in enumerate(CRITERIA, 1):
            value = getattr(structured, attr)
            if value:
                status, text = "satisfied", f"A {name} section is present."
                evidence = [Evidence(kind="report_excerpt", ref=f"report:{raw.report_id}", excerpt=value)]
            else:
                status, text = "not_satisfied", f"No {name} section was found."
                evidence = [Evidence(kind="note", ref=f"report:{raw.report_id}", excerpt=None)]
            findings.append(Finding(finding_id=f"{raw.report_id}-ie-{n}", report_id=raw.report_id,
                                    source="input_evaluation", subject=name, status=status,
                                    statement=PLACEHOLDER + text, evidence=evidence))
        requests = [InvestigationRequest(claim_id=f"{raw.report_id}-claim-{n}", report_id=raw.report_id,
                                         claim_text=ref)
                    for n, ref in enumerate(structured.code_references, 1)]
        return IEResult(report_id=raw.report_id, findings=findings, investigation_requests=requests)

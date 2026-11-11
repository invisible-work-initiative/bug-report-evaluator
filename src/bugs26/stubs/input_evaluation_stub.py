"""PLACEHOLDER Input Evaluation. The real IE subsystem (another team) replaces this.

It only checks whether each section exists (P = present, N = not found, U = unable to judge).
It does not judge quality.
"""
from ..integration.intake import line_of, meaningful_text
from ..integration.models import Evidence, Finding, IEResult, InvestigationRequest, RawReport, StructuredReport

PLACEHOLDER = "[PLACEHOLDER Input Evaluation] "
CRITERIA = [  # (id, structured field, name)
    ("C1", "description", "description"),
    ("C2", "steps_to_reproduce", "steps to reproduce"),
    ("C3", "expected_behavior", "expected behavior"),
    ("C4", "observed_behavior", "observed behavior"),
    ("C5", "environment", "environment"),
]
UNJUDGED = [("C6", "evidence"), ("C7", "clarity")]


class StubInputEvaluator:
    def evaluate(self, raw: RawReport, structured: StructuredReport) -> IEResult:
        rid, findings, present = raw.report_id, [], set()
        for cid, field, name in CRITERIA:
            sections = [s for s in structured.fields.get(field, []) if meaningful_text(s)]
            if sections:
                present.add(cid)
                status, text = "present", f"A {name} section is present."
                evidence = [Evidence(kind="report_excerpt", ref=f"report:{rid}", excerpt=s.text,
                                     start=s.start, end=s.end,
                                     line_start=line_of(raw.original_body, s.start),
                                     line_end=line_of(raw.original_body, max(s.start, s.end - 1))) for s in sections]
            else:
                status, text = "not_found", f"No {name} section was found."
                evidence = [Evidence(kind="note", ref=f"report:{rid}", excerpt="no matching section")]
            findings.append(Finding(finding_id=f"{rid}-{cid}", report_id=rid, source="input_evaluation",
                                    subject=f"{cid} {name}", status=status, statement=PLACEHOLDER + text,
                                    evidence=evidence))
        for cid, name in UNJUDGED:
            findings.append(Finding(finding_id=f"{rid}-{cid}", report_id=rid, source="input_evaluation",
                                    subject=f"{cid} {name}", status="unable_to_judge",
                                    statement=PLACEHOLDER + f"{name} is not judged by the placeholder.",
                                    evidence=[Evidence(kind="note", ref=f"report:{rid}", excerpt="not judged")]))

        missing = [name for cid, _, name in CRITERIA if cid in ("C2", "C3", "C4") and cid not in present]
        refs = structured.code_references
        if "C2" in present and ({"C3", "C4"} & present) and refs:
            decision, reason = "investigate", "Steps, expected or observed behavior, and code references are present."
        elif missing:
            decision, reason = "request_more_information", "Missing: " + ", ".join(missing) + "."
        else:
            decision, reason = "do_not_investigate", "No checkable claim: the report cites no code references."
        requests = [InvestigationRequest(claim_id=f"{rid}-claim-{n}", report_id=rid, claim_text=r.text,
                                         location={"start": r.start, "end": r.end},
                                         ie_context={"origin": "placeholder IE: code reference found in text"})
                    for n, r in enumerate(refs, 1)] if decision == "investigate" else []
        return IEResult(report_id=rid, decision=decision, reason=reason, missing_information=missing,
                        findings=findings, investigation_requests=requests,
                        not_checked=["C6/C7 not judged (placeholder)",
                                     "Content quality not judged - only section presence (placeholder)"])

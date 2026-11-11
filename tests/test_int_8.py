"""INT-8 Verification: transfer a finding and check that its evidence references remain unchanged."""
from bugs26.integration import pipeline
from bugs26.integration.models import CIResult, Evidence, Finding, IEResult, InvestigationRequest

EVIDENCE = [
    Evidence(kind="file", ref="src/a.py:10", excerpt="  odd   spacing\n"),
    Evidence(kind="url", ref="https://github.com/o/r/issues/1"),
    Evidence(kind="report_excerpt", ref="report:x", excerpt="e", start=3, end=4),
]


def finding(rid, source, fid):
    return Finding(finding_id=fid, report_id=rid, source=source, subject="x", status="present",
                   statement="s", evidence=list(EVIDENCE))


class FixedEvaluator:
    def evaluate(self, raw, structured):
        req = InvestigationRequest(claim_id="c", report_id=raw.report_id, claim_text="t")
        return IEResult(report_id=raw.report_id, decision="investigate", reason="r",
                        findings=[finding(raw.report_id, "input_evaluation", "f1")], investigation_requests=[req])


class FixedInvestigator:
    def investigate(self, request):
        return CIResult(report_id=request.report_id, findings=[finding(request.report_id, "claim_investigation", "f2")])


def test_evidence_unchanged_from_both_subsystems(good):
    out = pipeline.run(good, "paste", evaluator=FixedEvaluator(), investigator=FixedInvestigator())
    for fid in ("f1", "f2"):
        f = next(f for f in out.findings if f.finding_id == fid)
        assert f.evidence == EVIDENCE
    assert out.model_dump(mode="json")["findings"][0]["evidence"] == [e.model_dump(mode="json") for e in EVIDENCE]

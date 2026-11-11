"""INT-5 Verification: check that Integration receives findings from both subsystems."""
from bugs26.integration import pipeline
from bugs26.integration.models import CIResult, Finding, IEResult, InvestigationRequest


def finding(rid, source, fid):
    return Finding(finding_id=fid, report_id=rid, source=source, subject="s", status="present", statement="s")


class FakeEvaluator:
    def evaluate(self, raw, structured):
        req = InvestigationRequest(claim_id="c", report_id=raw.report_id, claim_text="t")
        return IEResult(report_id=raw.report_id, decision="investigate", reason="r",
                        findings=[finding(raw.report_id, "input_evaluation", "ie-1")], investigation_requests=[req])


class FakeInvestigator:
    def investigate(self, request):
        return CIResult(report_id=request.report_id, findings=[finding(request.report_id, "claim_investigation", "ci-1")])


def test_findings_from_both_subsystems(good):
    out = pipeline.run(good, "paste", evaluator=FakeEvaluator(), investigator=FakeInvestigator())
    assert [(f.finding_id, f.source) for f in out.findings] == [("ie-1", "input_evaluation"),
                                                                ("ci-1", "claim_investigation")]

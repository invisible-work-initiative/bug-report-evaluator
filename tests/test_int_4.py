"""INT-4 Verification: send a sample investigation request; CI receives it with the needed context."""
from bugs26.integration import pipeline
from bugs26.integration.models import CIResult, IEResult, InvestigationRequest


class OneRequestEvaluator:
    def evaluate(self, raw, structured):
        req = InvestigationRequest(claim_id="c1", report_id=raw.report_id, claim_text="load_config() crashes")
        return IEResult(report_id=raw.report_id, investigation_requests=[req])


class RecordingInvestigator:
    def __init__(self):
        self.requests = []

    def investigate(self, request):
        self.requests.append(request)
        return CIResult(report_id=request.report_id)


def test_ci_receives_request_with_context(good):
    ci = RecordingInvestigator()
    pipeline.run(good, "paste", repo_url="https://github.com/o/r",
                 evaluator=OneRequestEvaluator(), investigator=ci)
    (req,) = ci.requests
    assert req.claim_id == "c1" and req.claim_text == "load_config() crashes"
    assert req.context["repo_url"] == "https://github.com/o/r"
    assert any("2.4.1" in v for v in req.context["versions"])
    assert "Ubuntu 22.04" in req.context["environment"]
    assert "src/mytool/config.py:88" in req.context["code_references"]

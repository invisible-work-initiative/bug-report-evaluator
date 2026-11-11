"""INT-4 Verification: send a sample investigation request; CI receives it with the needed context."""
import pytest

from bugs26.integration import pipeline
from bugs26.integration.models import CIResult, IEResult, InvestigationRequest


def evaluator(decision="investigate", n_requests=1, report_id=None, reason="because"):
    class Ev:
        def evaluate(self, raw, structured):
            reqs = [InvestigationRequest(claim_id=f"c{i}", report_id=report_id or raw.report_id,
                                         claim_text="load_config() crashes", location={"start": 1, "end": 5},
                                         ie_context={"mine": [1, 2]}) for i in range(n_requests)]
            return IEResult(report_id=raw.report_id, decision=decision, reason=reason, investigation_requests=reqs)
    return Ev()


class RecordingInvestigator:
    def __init__(self):
        self.requests = []

    def investigate(self, request):
        self.requests.append(request)
        return CIResult(report_id=request.report_id, not_checked=["CI limit"])


def test_ci_receives_request_with_context(good):
    ci = RecordingInvestigator()
    out = pipeline.run(good, "paste", repo_url="https://github.com/o/r", evaluator=evaluator(), investigator=ci)
    (req,) = ci.requests
    assert req.claim_id == "c0" and req.claim_text == "load_config() crashes" and req.location == {"start": 1, "end": 5}
    assert req.context["repo_url"] == "https://github.com/o/r"
    assert set(req.context["fields"]) == {"description", "steps_to_reproduce", "expected_behavior",
                                          "observed_behavior", "environment"}
    assert "Ubuntu 22.04" in req.context["fields"]["environment"][0]
    assert req.ie_context == {"mine": [1, 2]}  # untouched
    assert "CI limit" in out.could_not_check


def test_report_id_mismatch_is_rejected(good):
    with pytest.raises(ValueError):
        pipeline.run(good, "paste", evaluator=evaluator(report_id="other"), investigator=RecordingInvestigator())


@pytest.mark.parametrize("decision", ["request_more_information", "do_not_investigate"])
def test_uc2_ci_skipped_unless_investigate(good, decision):
    ci = RecordingInvestigator()
    out = pipeline.run(good, "paste", evaluator=evaluator(decision, reason="no steps"), investigator=ci)
    assert ci.requests == []
    assert "Claims not investigated: no steps" in out.could_not_check
    assert out.ie_decision == decision


def test_uc3_ci_skipped_without_requests(good):
    ci = RecordingInvestigator()
    out = pipeline.run(good, "paste", evaluator=evaluator(n_requests=0), investigator=ci)
    assert ci.requests == []
    assert "No specific bug claim was identified" in out.could_not_check


def test_ci_failure_is_reported_and_the_run_continues(good):
    class Boom:
        def investigate(self, request):
            raise RuntimeError("cannot reach repo")
    out = pipeline.run(good, "paste", evaluator=evaluator(n_requests=2), investigator=Boom())
    assert out.could_not_check.count("Claim Investigation failed: RuntimeError: cannot reach repo") == 2
    assert out.findings == [] and out.ie_decision == "investigate"


def test_ie_failure_stops_with_an_error(good):
    from bugs26.integration.intake import InputEvaluationError

    class Boom:
        def evaluate(self, raw, structured):
            raise KeyError("x")
    with pytest.raises(InputEvaluationError, match="Input Evaluation failed: KeyError"):
        pipeline.run(good, "paste", evaluator=Boom())
def test_ci_answer_for_another_report_is_a_failure_not_a_finding(good):
    class Wrong:
        def investigate(self, request):
            return CIResult(report_id="other", findings=[])
    out = pipeline.run(good, "paste", evaluator=evaluator(), investigator=Wrong())
    assert any(c.startswith("Claim Investigation failed: ValueError") and "another report" in c
               for c in out.could_not_check)

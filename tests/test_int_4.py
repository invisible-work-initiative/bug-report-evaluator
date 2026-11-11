"""INT-4 Verification: send a sample investigation request; CI receives it with the needed context.
Routing is mechanical: one CI call per identified claim."""
import pytest

from bugs26.integration import pipeline
from bugs26.integration.intake import InputEvaluationError
from bugs26.integration.models import CIResult, IEClaimExtraction, IEDiagnostic, IEResult
from conftest import ci_result, ie_claim, ie_result


def evaluator(n_claims=1, **kw):
    class Ev:
        def evaluate(self, record):
            return ie_result(record, claims=[ie_claim(i) for i in range(n_claims)], **kw)
    return Ev()


class RecordingInvestigator:
    def __init__(self, **kw):
        self.requests, self.kw = [], kw

    def investigate(self, request):
        self.requests.append(request)
        return ci_result(request, **self.kw)


def test_ci_receives_request_with_context(good):
    ci = RecordingInvestigator()
    pipeline.run(good, "github", "https://github.com/o/r", title="T", issue_url="https://github.com/o/r/issues/7",
                 issue_number=7, evaluator=evaluator(), investigator=ci)
    (req,) = ci.requests
    assert (req.claim_id, req.claim_text, req.relevant_context, req.named_project_versions) == (
        "c0", "load_config() crashes", "load_config() crashes", ["1.2"])  # from IE, untouched
    assert (req.repository, req.issue_url, req.title, req.raw_body) == ("o/r", "https://github.com/o/r/issues/7", "T", good)
    assert req.request_id


def test_one_ci_call_per_claim(good):
    ci = RecordingInvestigator()
    out = pipeline.run(good, "paste", evaluator=evaluator(3), investigator=ci)
    assert [r.claim_id for r in ci.requests] == ["c0", "c1", "c2"]
    assert [r.claim_id for r in out.ci_results] == ["c0", "c1", "c2"]


def test_ci_skipped_when_no_checkable_claims(good):
    ci = RecordingInvestigator()
    out = pipeline.run(good, "paste", evaluator=evaluator(0), investigator=ci)
    assert ci.requests == [] and out.ci_results == []
    assert "No checkable claim was identified, so Claim Investigation was not called." in out.could_not_check


def test_ci_skipped_when_claim_extraction_not_performed(good):
    ci = RecordingInvestigator()
    ev = evaluator(0, processing_status="partial", no_checkable_claims=None,
                   claim_extraction=IEClaimExtraction(status="not_performed", reason="model down"),
                   diagnostics=[IEDiagnostic(severity="error", code="dependency_unavailable", message="model down")])
    out = pipeline.run(good, "paste", evaluator=ev, investigator=ci)
    assert ci.requests == []
    assert "Claims not investigated: claim extraction was not performed (model down)." in out.could_not_check
    assert "Claim extraction not_performed: model down" in out.could_not_check


@pytest.mark.parametrize("status", ["invalid_input", "failed"])
def test_ci_skipped_and_failure_shown_when_ie_rejected_or_failed(good, status):
    class Ev:
        def evaluate(self, record):
            return IEResult(request_id=record.request_id, snapshot_id=record.snapshot_id, processing_status=status,
                            claim_extraction=IEClaimExtraction(status="not_performed", reason="bad input"),
                            diagnostics=[IEDiagnostic(severity="error", code="invalid_value", path="/raw_body", message="bad raw_body")],
                            provenance=ie_result(record).provenance)
    ci = RecordingInvestigator()
    out = pipeline.run(good, "paste", evaluator=Ev(), investigator=ci)
    assert ci.requests == [] and out.ie.processing_status == status
    assert f"Input Evaluation status: {status}." in out.could_not_check  # never shown as a completed evaluation
    assert f"Claims not investigated: Input Evaluation returned {status}." in out.could_not_check
    assert "Input Evaluation error invalid_value: bad raw_body" in out.could_not_check


def test_ie_answer_for_another_request_is_a_failure(good):
    class Ev:
        def __init__(self, field):
            self.field = field

        def evaluate(self, record):
            return ie_result(record, **{self.field: "other"})
    for field in ("request_id", "snapshot_id"):
        with pytest.raises(InputEvaluationError, match="another request"):
            pipeline.run(good, "paste", evaluator=Ev(field), investigator=RecordingInvestigator())


def test_ie_result_without_seven_criteria_is_a_failure(good):
    class Ev:
        def evaluate(self, record):
            r = ie_result(record)
            return r.model_copy(update={"criterion_findings": r.criterion_findings[:6]})
    with pytest.raises(InputEvaluationError, match="C1-C7"):
        pipeline.run(good, "paste", evaluator=Ev())


def test_ci_failure_is_reported_and_the_run_continues(good):
    class Boom:
        def investigate(self, request):
            raise RuntimeError("cannot reach repo")
    out = pipeline.run(good, "paste", evaluator=evaluator(2), investigator=Boom())
    assert sum("Claim Investigation failed for claim 'load_config() crashes': RuntimeError: cannot reach repo" == c
               for c in out.could_not_check) == 2
    assert out.ci_results == [] and out.ie.criterion_findings  # IE findings are still shown


def test_ie_failure_stops_with_an_error(good):
    class Boom:
        def evaluate(self, record):
            raise KeyError("x")
    with pytest.raises(InputEvaluationError, match="Input Evaluation failed: KeyError"):
        pipeline.run(good, "paste", evaluator=Boom())


def test_ci_answer_for_another_claim_or_request_is_a_failure_not_a_result(good):
    for field in ("claim_id", "request_id"):
        class Wrong:
            def investigate(self, request):
                return ci_result(request).model_copy(update={field: "other"})
        out = pipeline.run(good, "paste", evaluator=evaluator(), investigator=Wrong())
        assert out.ci_results == []
        assert any("answered for another claim" in c for c in out.could_not_check)


@pytest.mark.parametrize("n", [0, 2])
def test_zero_or_several_findings_for_a_claim_is_a_failure(good, n):
    class Odd:
        def investigate(self, request):
            return ci_result(request, n_findings=n)
    out = pipeline.run(good, "paste", evaluator=evaluator(), investigator=Odd())
    assert out.ci_results == []
    assert any(f"returned {n} findings" in c and "exactly one" in c for c in out.could_not_check)


def test_ci_limit_and_insufficient_evidence_reach_could_not_check(good):
    out = pipeline.run(good, "paste", evaluator=evaluator(),
                       investigator=RecordingInvestigator(outcome="insufficient evidence", limitation="file not found"))
    assert "Claim 'load_config() crashes': insufficient evidence; file not found" in out.could_not_check
    ok = pipeline.run(good, "paste", evaluator=evaluator(), investigator=RecordingInvestigator())
    assert not any("load_config" in c for c in ok.could_not_check)

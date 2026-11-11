"""INT-4 Verification: send a sample investigation request; CI receives it with the needed context.
Routing is mechanical: one CI call per identified claim. Also: IE results are checked before anything is routed."""
import pytest

from bugs26.integration import pipeline
from bugs26.integration.intake import InputEvaluationError
from bugs26.integration.models import IEClaimExtraction, IEDiagnostic, IEResult, IEUnevaluatedReason
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


def error(code="internal_error", message="it broke"):
    return IEDiagnostic(severity="error", code=code, path=None, message=message)


def test_ci_receives_request_with_context(good):
    ci = RecordingInvestigator()
    out = pipeline.run(good, "github", "https://github.com/o/r", title="T", issue_url="https://github.com/o/r/issues/7",
                       issue_number=7, evaluator=evaluator(), investigator=ci)
    (req,) = ci.requests
    claim = out.ie.identified_claims[0]
    # the claim is forwarded untouched, all five parts (IF-10)
    assert (req.claim_id, req.claim_text, req.source, req.relevant_context, req.named_project_versions) == (
        claim.claim_id, claim.claim_text, claim.source, claim.relevant_context, claim.named_project_versions)
    assert (req.repository, req.issue_url, req.title, req.raw_body) == ("o/r", "https://github.com/o/r/issues/7", "T", good)
    assert (req.request_id, req.snapshot_id) == (out.record.request_id, out.record.snapshot_id)


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
                   diagnostics=[error("dependency_unavailable", "model down")])
    out = pipeline.run(good, "paste", evaluator=ev, investigator=ci)
    assert ci.requests == []
    assert "Claims not investigated: claim extraction was not performed (model down)." in out.could_not_check
    assert "Claim extraction not_performed: model down" in out.could_not_check


@pytest.mark.parametrize("status", ["invalid_input", "failed"])
def test_ci_skipped_and_failure_shown_when_ie_rejected_or_failed(good, status):
    class Ev:
        def evaluate(self, record):
            ok = ie_result(record)
            return ok.model_copy(update=dict(
                processing_status=status, criterion_findings=[], identified_claims=[], no_checkable_claims=None,
                claim_extraction=IEClaimExtraction(status="not_performed", reason="bad input"),
                diagnostics=[error("invalid_value", "bad raw_body")]))
    ci = RecordingInvestigator()
    out = pipeline.run(good, "paste", evaluator=Ev(), investigator=ci)
    assert ci.requests == [] and out.ie.processing_status == status  # shown as a failure, in the banner and the JSON
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


def inconsistent(mutate, why):
    """An IE result that breaks the draft's section 4.2 rules must stop the run, never be shown as findings."""
    class Ev:
        def evaluate(self, record):
            return mutate(ie_result(record, claims=[ie_claim(1)]))
    with pytest.raises(InputEvaluationError, match=why):
        pipeline.run("x", "paste", evaluator=Ev(), investigator=RecordingInvestigator())


def unevaluate(r, i=5, listed=True):
    f = r.criterion_findings[i].model_copy(update=dict(
        evaluation_status="unevaluated", rating=None, unevaluated_reason=IEUnevaluatedReason(code="internal_error", message="x")))
    return r.model_copy(update=dict(criterion_findings=r.criterion_findings[:i] + [f] + r.criterion_findings[i + 1:],
                                    unevaluated_criteria=[f.criterion_id] if listed else []))


@pytest.mark.parametrize("name, mutate, why", [
    ("six findings", lambda r: r.model_copy(update=dict(criterion_findings=r.criterion_findings[:6])), "C1-C7"),
    ("completed with an unevaluated criterion", lambda r: unevaluate(r), "completed needs"),
    ("partial without an error diagnostic", lambda r: unevaluate(r).model_copy(update=dict(processing_status="partial")), "partial needs"),
    ("unevaluated_criteria does not list it", lambda r: unevaluate(r, listed=False).model_copy(update=dict(
        processing_status="partial", diagnostics=[error()])), "unevaluated_criteria"),
    ("rating on an unevaluated finding", lambda r: r.model_copy(update=dict(
        processing_status="partial", diagnostics=[error()], unevaluated_criteria=["C1"], criterion_findings=[
        r.criterion_findings[0].model_copy(update=dict(evaluation_status="unevaluated"))] + r.criterion_findings[1:])), "rating"),
    ("criteria_version differs from provenance", lambda r: r.model_copy(update=dict(provenance=r.provenance.model_copy(
        update=dict(criteria_version="v2")))), "criteria_version"),
    ("claim quote differs from claim_text", lambda r: r.model_copy(update=dict(identified_claims=[
        r.identified_claims[0].model_copy(update=dict(claim_text="other"))])), "quotation"),
    ("no_checkable_claims true with claims", lambda r: r.model_copy(update=dict(no_checkable_claims=True)), "no_checkable_claims"),
    ("repeated claim_id", lambda r: r.model_copy(update=dict(identified_claims=r.identified_claims * 2)), "repeated"),
    ("invalid_input with findings", lambda r: r.model_copy(update=dict(
        processing_status="invalid_input", diagnostics=[error()],
        claim_extraction=IEClaimExtraction(status="not_performed", reason="r"))), "invalid_input needs"),
])
def test_inconsistent_ie_result_is_a_failure(name, mutate, why):
    inconsistent(mutate, why)


def test_ie_result_of_the_wrong_type_is_a_failure(good):
    class Ev:
        def evaluate(self, record):
            return {"processing_status": "completed"}
    with pytest.raises(InputEvaluationError, match="Input Evaluation failed: ValidationError"):
        pipeline.run(good, "paste", evaluator=Ev())


def test_ci_failure_is_reported_as_not_investigated_and_the_run_continues(good):
    class Boom:
        def investigate(self, request):
            raise RuntimeError("cannot reach repo")
    out = pipeline.run(good, "paste", evaluator=evaluator(2), investigator=Boom())
    assert out.could_not_check.count("Claim 'load_config()' not investigated: RuntimeError: cannot reach repo") == 2
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
    assert "Claim 'load_config()': insufficient evidence; file not found" in out.could_not_check
    ok = pipeline.run(good, "paste", evaluator=evaluator(), investigator=RecordingInvestigator())
    assert not any("load_config" in c for c in ok.could_not_check)


def test_ci_result_may_carry_extra_fields_ci_schema_is_open(good):
    class Extra:
        def investigate(self, request):
            r = ci_result(request)
            return type(r).model_validate({**r.model_dump(), "checked_version": "1.2", "search_record": ["a"]})
    out = pipeline.run(good, "paste", evaluator=evaluator(), investigator=Extra())
    assert out.model_dump(mode="json")["ci_results"][0]["checked_version"] == "1.2"

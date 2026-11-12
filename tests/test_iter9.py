"""Iteration 9 review fixes: R4 diagnostics, lenient-where-the-draft-is-silent IE checks, CI validation, blank values."""
import pytest

from bugs26.integration import intake, pipeline
from bugs26.integration.intake import InputEvaluationError
from bugs26.integration.models import IEClaimExtraction, IEDiagnostic, IELines, IEUnevaluatedReason
from conftest import ci_result, ie_claim, ie_result


def error(code="internal_error", message="it broke"):
    return IEDiagnostic(severity="error", code=code, path=None, message=message)


def unevaluate(r, ids):
    fs = [f.model_copy(update=dict(evaluation_status="unevaluated", rating=None, unevaluated_reason=IEUnevaluatedReason(
        code="internal_error", message=f"{f.criterion_id} down"))) if f.criterion_id in ids else f for f in r.criterion_findings]
    return r.model_copy(update=dict(criterion_findings=fs, unevaluated_criteria=ids, processing_status="partial"))


def claim_on_line_1():
    c = ie_claim(1)  # the report below is one line, so the claim's quotation is on line 1
    return c.model_copy(update=dict(source=c.source.model_copy(update=dict(lines=IELines(start=1, end=1)))))


def ev(fn):
    class E:
        def evaluate(self, record):
            return fn(ie_result(record, claims=[claim_on_line_1()]))
    return E()


class OkCI:
    def investigate(self, request):
        return ci_result(request)


def run(fn, ci=None):
    return pipeline.run("load_config() crashes", "paste", evaluator=ev(fn), investigator=ci or OkCI())


def test_error_diagnostic_is_hidden_only_when_its_message_equals_an_unevaluated_reason():
    same = error("internal_error", "C6 down")
    other = error("internal_error", "a different failure")  # same code, other message: must not be hidden (R4)
    out = run(lambda r: unevaluate(r, ["C6"]).model_copy(update=dict(diagnostics=[same, other])))
    assert "Input Evaluation error internal_error: a different failure" in out.could_not_check
    assert not any(c.startswith("Input Evaluation error") and "C6 down" in c for c in out.could_not_check)
    assert "C6 not evaluated (internal_error): C6 down" in out.could_not_check


@pytest.mark.parametrize("status", ["invalid_input", "failed"])
def test_failed_or_invalid_ie_says_no_criterion_was_evaluated(status):
    def mutate(r):
        return r.model_copy(update=dict(processing_status=status, criterion_findings=[], identified_claims=[],
                                        no_checkable_claims=None, diagnostics=[error()],
                                        claim_extraction=IEClaimExtraction(status="not_performed", reason="r")))
    out = run(mutate)
    assert f"No criterion was evaluated: Input Evaluation returned {status}." in out.could_not_check
    assert not any(c.startswith("No criterion") for c in run(lambda r: r).could_not_check)


def test_ie_check_ignores_finding_order_and_unevaluated_order_but_not_duplicates():
    out = run(lambda r: unevaluate(r, ["C7", "C6"]).model_copy(update=dict(
        criterion_findings=list(reversed(unevaluate(r, ["C7", "C6"]).criterion_findings)), diagnostics=[error()])))
    assert out.ie.processing_status == "partial"
    with pytest.raises(InputEvaluationError, match="unevaluated_criteria"):
        run(lambda r: unevaluate(r, ["C6"]).model_copy(update=dict(unevaluated_criteria=["C6", "C6"], diagnostics=[error()])))
    with pytest.raises(InputEvaluationError, match="C1-C7"):
        run(lambda r: r.model_copy(update=dict(criterion_findings=r.criterion_findings[:6] + r.criterion_findings[:1])))


def test_no_checkable_claims_rules():
    partial = dict(processing_status="partial", diagnostics=[error()],
                   claim_extraction=IEClaimExtraction(status="partial", reason="cut off"))
    assert run(lambda r: r.model_copy(update=dict(no_checkable_claims=False, **partial))).ie.no_checkable_claims is False  # claims found
    for bad in (None, True):  # claims present must say false
        with pytest.raises(InputEvaluationError, match="no_checkable_claims"):
            run(lambda r: r.model_copy(update=dict(no_checkable_claims=bad, **partial)))
    no_claims = lambda v: lambda r: r.model_copy(update=dict(identified_claims=[], no_checkable_claims=v))
    assert run(no_claims(True)).ie.no_checkable_claims is True
    with pytest.raises(InputEvaluationError, match="no_checkable_claims"):
        run(no_claims(None))  # extraction completed and no claims: must be true
    assert run(lambda r: r.model_copy(update=dict(identified_claims=[], no_checkable_claims=None, **partial))).ie.no_checkable_claims is None


def test_null_ids_of_an_invalid_input_result_are_accepted_per_field():
    def mutate(null_field):
        def f(r):
            return r.model_copy(update=dict(
                processing_status="invalid_input", criterion_findings=[], identified_claims=[], no_checkable_claims=None,
                diagnostics=[error()], claim_extraction=IEClaimExtraction(status="not_performed", reason="r"),
                **{null_field: None}))
        return f
    assert run(mutate("request_id")).ie.request_id is None and run(mutate("snapshot_id")).ie.snapshot_id is None
    with pytest.raises(InputEvaluationError, match="another request"):  # a null id is not accepted for a normal result
        run(lambda r: r.model_copy(update=dict(request_id=None)))


def test_ci_answer_is_validated_inside_the_try():
    class Dict:
        def investigate(self, request):
            return {"claim_id": request.claim_id, "findings": [{"claim_id": request.claim_id}]}  # no outcome
    out = run(lambda r: r, Dict())
    assert out.ci_results == []
    assert any("not investigated: ValidationError" in c for c in out.could_not_check)


def test_ci_request_id_is_optional_but_checked_when_present():
    class NoId:
        def investigate(self, request):
            return ci_result(request).model_copy(update=dict(request_id=None))
    out = run(lambda r: r, NoId())
    assert [r.request_id for r in out.ci_results] == [None] and out.record.request_id


def test_zero_findings_keeps_the_limitation_text():
    class Zero:
        def investigate(self, request):
            return ci_result(request, n_findings=0, limitation="repository not reachable")
    out = run(lambda r: r, Zero())
    assert out.ci_results == []
    assert any("returned 0 findings" in c and "repository not reachable" in c for c in out.could_not_check)


def test_blank_value_leaves_out_its_final_line_break_and_lies_inside_its_lines():
    for nl in ("\n", "\r\n"):
        body = nl.join(["### A", "   ", "### B", "x", ""])
        raw = intake.receive(body, "paste")
        s = intake.structure(raw)
        intake.verify_structured(raw, s)
        a = s.sections[0]
        assert (a.status, a.value, (a.source_lines.start, a.source_lines.end)) == ("blank", "   ", (1, 2))
    raw = intake.receive("### A\n### B\nx", "paste")
    s = intake.structure(raw)
    assert (s.sections[0].value, s.sections[0].source_lines.end) == ("", 1)  # empty blank mid-body: the heading line only


def test_stub_messages_do_not_repeat_the_criterion_id():
    out = pipeline.run("## Steps\nx", "paste")
    msgs = [f.unevaluated_reason.message for f in out.ie.criterion_findings if f.unevaluated_reason]
    assert msgs and not any(m.startswith("C") and m[1].isdigit() for m in msgs)


def test_output_records_the_ci_requests_actually_sent():
    """INT-4/INT-8: the output carries each CI request exactly as sent, so the page can show every handoff."""
    seen = []

    class RecordingCI:
        def investigate(self, request):
            seen.append(request)
            return ci_result(request)

    out = run(lambda r: r, RecordingCI())
    assert out.ci_requests == seen and len(seen) == 1
    assert out.ci_requests[0].claim_id == "c1" and out.ci_requests[0].source.lines.start == 1


def test_skipped_routing_sends_no_ci_request():
    out = run(lambda r: r.model_copy(update=dict(identified_claims=[], no_checkable_claims=True)))
    assert out.ci_requests == [] and out.ci_results == []

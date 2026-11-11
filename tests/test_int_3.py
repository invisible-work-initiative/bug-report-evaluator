"""INT-3 Verification: check that Input Evaluation receives both versions of the report."""
from bugs26.integration import pipeline
from bugs26.integration.models import IEResult


class RecordingEvaluator:
    def evaluate(self, raw, structured):
        self.raw, self.structured = raw, structured
        return IEResult(report_id=raw.report_id)


def test_ie_receives_original_and_structured(good):
    ie = RecordingEvaluator()
    pipeline.run(good, "paste", evaluator=ie)
    assert ie.raw.original_body == good
    assert ie.structured.fields["steps_to_reproduce"]
    assert ie.raw.report_id == ie.structured.report_id


def test_stub_ie_finds_code_references_not_integration():
    from bugs26.integration import intake
    from bugs26.stubs.input_evaluation_stub import find_code_references
    assert not hasattr(intake.structure(intake.receive("x", "paste")), "code_references")
    body = "`NaN` `float` `3.11` `df.dropna()` `a_b` `src/x.py` see https://github.com/o/r/blob/m/a/b.py and c.js:4 and f()"
    assert [t for t, _, _ in find_code_references(body)] == ["df.dropna()", "a_b", "src/x.py", "c.js:4", "f()"]

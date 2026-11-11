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
    assert ie.structured.title == "Crash when parsing empty config file"
    assert ie.raw.report_id == ie.structured.report_id

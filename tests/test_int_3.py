"""INT-3 Verification: check that Input Evaluation receives both versions of the report."""
from bugs26.integration import pipeline
from bugs26.integration.models import IEReportRecord
from conftest import ie_result


class RecordingEvaluator:
    def evaluate(self, record):
        self.record = record
        return ie_result(record)


def test_ie_receives_original_and_structured(good):
    ie = RecordingEvaluator()
    pipeline.run(good, "paste", evaluator=ie)
    r = ie.record
    assert isinstance(r, IEReportRecord) and r.schema_version == "1.0"
    assert r.raw_body == good  # the original, exact
    assert [s.semantic_concept for s in r.sections if s.semantic_concept == "steps_to_reproduce"]  # the structured version
    assert r.extraction.mode == "structured" and r.request_id and r.snapshot_id and r.body_source == "current"
    assert not any(k in r.model_dump() for k in ("report_id", "sha256", "source", "received_at"))  # Integration-internal


def test_free_form_report_is_sent_with_no_sections():
    ie = RecordingEvaluator()
    pipeline.run("It does not work.", "paste", evaluator=ie)
    assert ie.record.sections == [] and ie.record.extraction.mode == "free_form" and ie.record.raw_body == "It does not work."


def test_github_metadata_is_sent():
    ie = RecordingEvaluator()
    pipeline.run("## Steps\nx", "github", "https://github.com/o/r", title="T", issue_url="https://github.com/o/r/issues/7",
                 issue_number=7, labels=["bug"], created_at="2026-11-01T14:00:00Z", updated_at="2026-11-02T09:30:00Z", evaluator=ie)
    r = ie.record
    assert (r.repository, r.issue_number, r.issue_url, r.title, r.labels, r.created_at) == (
        "o/r", 7, "https://github.com/o/r/issues/7", "T", ["bug"], "2026-11-01T14:00:00Z")


def test_stub_ie_finds_code_references_not_integration():
    from bugs26.integration import intake
    from bugs26.stubs.input_evaluation_stub import find_code_references
    assert not hasattr(intake.structure(intake.receive("x", "paste")), "code_references")
    body = "`NaN` `float` `3.11` `df.dropna()` `a_b` `src/x.py` see https://github.com/o/r/blob/m/a/b.py and c.js:4 and f()"
    assert [t for t, _, _ in find_code_references(body)] == ["df.dropna()", "a_b", "src/x.py", "c.js:4", "f()"]

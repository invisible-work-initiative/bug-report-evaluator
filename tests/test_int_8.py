"""INT-8 Verification: transfer a finding and check that its evidence references remain unchanged."""
from bugs26.integration import pipeline
from bugs26.integration.models import Evidence, Finding, IEResult

EVIDENCE = [
    Evidence(kind="file", ref="src/a.py:10", excerpt="  odd   spacing\n"),
    Evidence(kind="url", ref="https://github.com/o/r/issues/1"),
]


class FixedEvaluator:
    def evaluate(self, raw, structured):
        f = Finding(finding_id="f1", report_id=raw.report_id, source="input_evaluation",
                    subject="x", status="satisfied", statement="s", evidence=list(EVIDENCE))
        return IEResult(report_id=raw.report_id, findings=[f])


def test_evidence_unchanged(good):
    out = pipeline.run(good, "paste", evaluator=FixedEvaluator())
    f = next(f for f in out.findings if f.finding_id == "f1")
    assert f.evidence == EVIDENCE
    assert out.model_dump(mode="json")["findings"][0]["evidence"] == [e.model_dump(mode="json") for e in EVIDENCE]

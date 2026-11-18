"""INT-5 Verification: check that Integration receives findings from both subsystems."""
from integration import pipeline
from conftest import ci_result, ie_claim, ie_result


class FakeEvaluator:
    def evaluate(self, record):
        return ie_result(record, claims=[ie_claim(1)])


class FakeInvestigator:
    def investigate(self, request):
        return ci_result(request, outcome="contradicted")


def test_findings_from_both_subsystems(good):
    out = pipeline.run(good, "paste", evaluator=FakeEvaluator(), investigator=FakeInvestigator())
    assert [f.criterion_id for f in out.ie.criterion_findings] == [f"C{i}" for i in range(1, 8)]
    assert [(r.claim_id, r.findings[0].outcome) for r in out.ci_results] == [("c1", "contradicted")]

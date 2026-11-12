"""INT-8 Verification: transfer a finding and check that its evidence references remain unchanged."""
from integration import pipeline
from integration.models import CIEvidence, CIFinding, CIResult, IELines
from conftest import ie_claim, ie_evidence, ie_result

IE_EVIDENCE = [
    ie_evidence("  odd   spacing\n", basis="source_reference", source="raw_body", section_id="s9", lines=IELines(start=3, end=4),
                quote="  odd \t spacing\n"),
    ie_evidence("none", basis="source_reference", source="title"),
]
CI_EVIDENCE = [
    CIEvidence(type="file", reference="src/a.py:10", explanation="  odd   spacing\n"),
    CIEvidence(type="url", reference="https://github.com/o/r/issues/1", explanation="x"),
]


class FixedEvaluator:
    def evaluate(self, record):
        self.sent = ie_result(record, claims=[ie_claim(1)])
        self.sent.criterion_findings[0].evidence[:] = IE_EVIDENCE
        return self.sent


class FixedInvestigator:
    def investigate(self, request):
        self.sent = CIResult(request_id=request.request_id, claim_id=request.claim_id, limitation="odd  limit",
                             findings=[CIFinding(claim_id=request.claim_id, outcome="supported", explanation="e",
                                                 evidence=list(CI_EVIDENCE))])
        return self.sent


def test_ie_and_ci_results_pass_through_unchanged(good):
    ie, ci = FixedEvaluator(), FixedInvestigator()
    out = pipeline.run(good, "paste", evaluator=ie, investigator=ci)
    assert out.ie == ie.sent and out.ci_results == [ci.sent]  # whole objects, not rebuilt
    assert out.ie.criterion_findings[0].evidence == IE_EVIDENCE
    assert out.ci_results[0].findings[0].evidence == CI_EVIDENCE
    dumped = out.model_dump(mode="json")
    assert dumped["ie"]["criterion_findings"][0]["evidence"] == [e.model_dump(mode="json") for e in IE_EVIDENCE]
    assert dumped["ci_results"][0]["findings"][0]["evidence"] == [e.model_dump(mode="json") for e in CI_EVIDENCE]

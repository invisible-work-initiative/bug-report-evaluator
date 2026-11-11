"""INT-7 Verification: each finding, claim, and evidence item is linked to the correct report (by request_id)."""
import pytest

from bugs26.integration import assemble, intake, pipeline
from conftest import ci_result, ie_result, sample


class FakeCI:
    def investigate(self, request):
        return ci_result(request)


def test_everything_links_to_its_report():
    a = pipeline.run(sample("good-report.md"), "paste", investigator=FakeCI())
    b = pipeline.run(sample("good-report.md"), "paste", investigator=FakeCI())
    assert a.record.request_id != b.record.request_id and a.record.snapshot_id != b.record.snapshot_id
    for out in (a, b):
        assert (out.ie.request_id, out.ie.snapshot_id) == (out.record.request_id, out.record.snapshot_id)
        assert out.ie.criterion_findings and out.ie.identified_claims
        section_ids = {s.section_id for s in out.record.sections}
        for f in out.ie.criterion_findings:
            assert f.evidence
            assert all(e.section_id is None or e.section_id in section_ids for e in f.evidence)
        for c in out.ie.identified_claims:  # a claim links to its line (R3)
            assert c.source.section_id in section_ids | {None}
            line = out.record.raw_body.split("\n")[c.source.lines.start - 1]
            assert c.source.quote == c.claim_text and c.claim_text in line
        assert {r.claim_id for r in out.ci_results} == {c.claim_id for c in out.ie.identified_claims}
        for r in out.ci_results:  # CI results are keyed by (request_id, claim_id)
            assert r.request_id == out.record.request_id and all(f.claim_id == r.claim_id for f in r.findings)


def test_ci_result_for_another_request_is_rejected():
    raw = intake.receive("x", "paste")
    out = pipeline.run("x", "paste")
    stray = ci_result(type("R", (), {"request_id": "other", "claim_id": "c"})())
    with pytest.raises(ValueError):
        assemble.build_output(raw, out.record, ie_result(out.record), [stray], [], [])

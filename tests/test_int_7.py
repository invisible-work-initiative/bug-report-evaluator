"""INT-7 Verification: each finding, claim, and evidence item is linked to the correct report."""
import pytest

from bugs26.integration import assemble, intake, pipeline
from conftest import ci_result, sample


def test_everything_links_to_its_report():
    a = pipeline.run(sample("good-report.md"), "paste")
    b = pipeline.run(sample("good-report.md"), "paste")
    assert a.report_id != b.report_id and a.request_id != b.request_id and a.snapshot_id != b.snapshot_id
    for out in (a, b):
        assert out.ie.request_id == out.request_id and out.ie.snapshot_id == out.snapshot_id
        assert out.ie.criterion_findings and out.ie.identified_claims
        section_ids = {s.section_id for s in out.structured.sections}
        for f in out.ie.criterion_findings:
            assert f.evidence
            assert all(e.section_id is None or e.section_id in section_ids for e in f.evidence)
        for c in out.ie.identified_claims:  # a claim links to its line (R3)
            assert c.source.section_id in section_ids | {None}
            line = out.raw_body.split("\n")[c.source.lines.start - 1]
            assert c.source.quote == c.claim_text and c.claim_text in line
        assert {r.claim_id for r in out.ci_results} == {c.claim_id for c in out.ie.identified_claims}
        for r in out.ci_results:  # CI results are keyed by (request_id, claim_id)
            assert r.request_id == out.request_id and all(f.claim_id == r.claim_id for f in r.findings)
        assert out.structured.report_id == out.report_id


def test_ci_result_for_another_request_is_rejected():
    raw = intake.receive("x", "paste")
    out = pipeline.run("x", "paste")
    stray = ci_result(type("R", (), {"request_id": "other", "claim_id": "c"})())
    with pytest.raises(ValueError):
        assemble.build_output(raw, out.structured, out.ie, [stray], [])

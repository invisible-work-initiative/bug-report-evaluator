"""INT-7 Verification: each finding, claim, and evidence item is linked to the correct report."""
import pytest

from bugs26.integration import assemble, pipeline
from bugs26.integration.models import CIResult, Finding, IEResult, InvestigationRequest
from conftest import sample


def test_everything_links_to_its_report():
    a = pipeline.run(sample("good-report.md"), "paste")
    b = pipeline.run(sample("good-report.md"), "paste")
    assert a.report_id != b.report_id
    for out in (a, b):
        assert out.findings
        for f in out.findings:
            assert f.report_id == out.report_id
            assert f.finding_id.startswith(out.report_id)
            assert f.evidence
            for e in f.evidence:
                assert e.ref == f"report:{out.report_id}"
        assert out.structured.report_id == out.report_id
        for f in (f for f in out.findings if f.source == "claim_investigation"):  # claims link to their lines (R3)
            e = f.evidence[0]
            assert e.kind == "report_excerpt" and out.original_body[e.start:e.end] == e.excerpt == f.subject


def test_finding_for_another_report_is_rejected():
    stray = Finding(finding_id="x", report_id="other", source="input_evaluation",
                    subject="s", status="present", statement="s")
    with pytest.raises(ValueError):
        assemble.collect("mine", IEResult(report_id="mine", findings=[stray]), CIResult(report_id="mine"))


def test_request_for_another_report_is_rejected(good):
    class Ev:
        def evaluate(self, raw, structured):
            req = InvestigationRequest(claim_id="c", report_id="other", claim_text="x")
            return IEResult(report_id=raw.report_id, decision="investigate", investigation_requests=[req])
    with pytest.raises(ValueError):
        pipeline.run(good, "paste", evaluator=Ev())

"""INT-7 Verification: each finding, claim, and evidence item is linked to the correct report."""
import pytest

from bugs26.integration import assemble, pipeline
from bugs26.integration.models import CIResult, Finding, IEResult


def test_everything_links_to_its_report(good):
    a = pipeline.run(good, "paste")
    b = pipeline.run(good, "paste")
    assert a.report_id != b.report_id
    for out in (a, b):
        for f in out.findings:
            assert f.report_id == out.report_id
            assert f.finding_id.startswith(out.report_id)  # ids carry the report id
            for e in f.evidence:
                assert e.ref.startswith("report:" + out.report_id) or e.kind == "note"


def test_finding_for_another_report_is_rejected():
    stray = Finding(finding_id="x", report_id="other", source="input_evaluation",
                    subject="s", status="satisfied", statement="s")
    with pytest.raises(ValueError):
        assemble.collect("mine", IEResult(report_id="mine", findings=[stray]), CIResult(report_id="mine"))

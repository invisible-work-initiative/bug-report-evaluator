"""INT-6 Verification: output includes the collected findings and reaches the maintainer-facing interface."""
from fastapi.testclient import TestClient

from bugs26.integration import pipeline
from bugs26.web.app import app


def test_output_includes_collected_findings_and_r4(good):
    out = pipeline.run(good, "paste")
    assert len(out.ie.criterion_findings) == 7 and len(out.ci_results) == 3
    assert out.could_not_check  # R4: always present
    assert out.raw_body == good and out.structured.report_id == out.report_id
    assert any(c.startswith("C6 not evaluated") for c in out.could_not_check)  # IE limits reach the maintainer (R4)
    assert any("PLACEHOLDER Claim Investigation" in c and "no code was examined" in c for c in out.could_not_check)


def test_output_reaches_maintainer_interface(good):
    r = TestClient(app).post("/api/evaluate", data={"text": good})
    assert r.status_code == 200
    body = r.json()
    assert len(body["ie"]["criterion_findings"]) == 7 and len(body["ci_results"]) == 3
    assert body["could_not_check"] and body["ie"]["processing_status"] == "partial"

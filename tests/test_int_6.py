"""INT-6 Verification: output includes the collected findings and reaches the maintainer-facing interface."""
from fastapi.testclient import TestClient

from bugs26.integration import pipeline
from bugs26.web.app import app


def test_output_includes_collected_findings_and_r4(good):
    out = pipeline.run(good, "paste")
    assert len(out.findings) > 0
    assert out.could_not_check  # R4: always present
    assert out.original_body == good and out.structured.report_id == out.report_id
    assert "Claim Investigation is a placeholder: no code was examined" in out.could_not_check
    assert "C6/C7 not judged (placeholder)" in out.could_not_check  # IE limits reach the maintainer (R4)


def test_output_reaches_maintainer_interface(good):
    r = TestClient(app).post("/api/evaluate", data={"text": good})
    assert r.status_code == 200
    body = r.json()
    assert len(body["findings"]) > 0 and body["could_not_check"] and body["ie_decision"] == "investigate"

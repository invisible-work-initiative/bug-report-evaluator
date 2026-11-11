"""INT-6 Verification: output includes the collected findings and reaches the maintainer-facing interface."""
from fastapi.testclient import TestClient

from bugs26.integration import pipeline
from bugs26.web.app import app


def test_output_includes_collected_findings_and_r4(good):
    out = pipeline.run(good, "paste")
    assert len(out.findings) > 0
    assert sum(out.summary.values()) == len(out.findings)
    assert out.could_not_check  # R4: always present


def test_output_reaches_maintainer_interface(good):
    r = TestClient(app).post("/api/evaluate", data={"text": good})
    assert r.status_code == 200
    body = r.json()
    assert len(body["findings"]) > 0 and body["could_not_check"]

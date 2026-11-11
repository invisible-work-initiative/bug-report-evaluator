"""INT-6 Verification: output includes the collected findings and reaches the maintainer-facing interface."""
from fastapi.testclient import TestClient

from bugs26.integration import pipeline
from bugs26.web.app import app
from conftest import ci_result


class FakeCI:
    def investigate(self, request):
        return ci_result(request, outcome="insufficient evidence", limitation="file not found")


def test_output_includes_collected_findings_and_r4(good):
    out = pipeline.run(good, "paste", investigator=FakeCI())
    assert len(out.ie.criterion_findings) == 7 and len(out.ci_results) == 3
    assert out.could_not_check  # R4: always present
    assert out.record.raw_body == good and out.record.sections  # the snapshot (IE 4.3) is in the output
    assert any(c.startswith("C6 not evaluated") for c in out.could_not_check)  # IE limits reach the maintainer (R4)
    assert any("insufficient evidence; file not found" in c for c in out.could_not_check)


def test_stubs_are_labelled_and_claims_are_listed_as_not_investigated(good):
    out = pipeline.run(good, "paste")
    assert out.placeholders == ["Input Evaluation", "Claim Investigation"] and out.ci_results == []
    assert sum("not investigated: NotImplementedError: Claim Investigation not connected" in c for c in out.could_not_check) == 3
    assert pipeline.run(good, "paste", evaluator=type("E", (), {"evaluate": lambda s, r: __import__("conftest").ie_result(r)})(),
                        investigator=FakeCI()).placeholders == []


def test_output_reaches_maintainer_interface(good):
    r = TestClient(app).post("/api/evaluate", data={"text": good})
    assert r.status_code == 200
    body = r.json()
    assert len(body["ie"]["criterion_findings"]) == 7 and body["ie"]["processing_status"] == "partial"
    assert body["could_not_check"] and body["record"]["raw_body"] == good
    assert "spans" not in str(body.keys()) and "spans" not in body["record"]  # Integration-internal, not in the JSON

"""Integration's side of the Claim Investigation agreement, section 7 (CI-IN-01..06) and section 5.3.

Source: origin/claim-investigation, documentation/claim_investigation_interface_agreement.md. The real CI is not
connected, so a fake CI stands in for "Claim Investigation" in each test. The fake returns results in the CI shape.
"""
import re

from fastapi.testclient import TestClient

from bugs26.integration import pipeline
from bugs26.integration.models import CIEvidence, CIFinding, CIResult
from bugs26.web import app as web
from conftest import sample


def evidence_for(request):
    """Distinct, recognisable evidence per claim, so mix-ups are visible."""
    return CIEvidence(type="file path", reference=f"src/evidence_for_{request.claim_id}.py",
                      explanation=f"checked {request.claim_id}")


class FakeCI:
    """Answers each claim; claims listed in `insufficient` get insufficient evidence with a reason."""
    def __init__(self, insufficient=(), extra=None):
        self.insufficient, self.extra, self.seen = set(insufficient), extra or {}, []

    def investigate(self, request):
        self.seen.append(request)
        if request.claim_id in self.insufficient:
            return CIResult(request_id=request.request_id, claim_id=request.claim_id, limitation="repository mirror unavailable",
                            findings=[CIFinding(claim_id=request.claim_id, outcome="insufficient evidence",
                                                explanation="could not read the file")])
        return CIResult(request_id=request.request_id, claim_id=request.claim_id, **self.extra,
                        findings=[CIFinding(claim_id=request.claim_id, outcome="supported", explanation="found it",
                                            evidence=[evidence_for(request)])])


def run(ci):
    return pipeline.run(sample("good-report.md"), "paste", investigator=ci)


def page(ci, monkeypatch):
    """Render the maintainer page with this fake CI in place of the stub."""
    real = pipeline.run
    monkeypatch.setattr(web.pipeline, "run", lambda *a, **k: real(*a, **{**k, "investigator": ci}))
    r = TestClient(web.app).post("/evaluate", data={"text": sample("good-report.md")})
    assert r.status_code == 200
    return r.text


def claim_rows(html):
    """The rows of the Claims table, one per claim."""
    table = html.split("<h2>Claims</h2>", 1)[1].split("</table>", 1)[0]
    return re.findall(r"<tr>\s*<td><code>.*?</tr>", table, flags=re.S)


def test_CI_IN_01_completed_result_is_transferred():
    """CI-IN-01 Test: verify that a completed investigation result can be successfully transferred to Integration."""
    ci = FakeCI()
    out = run(ci)
    assert ci.seen and len(out.ci_results) == len(ci.seen)
    assert all(r.findings[0].outcome == "supported" for r in out.ci_results)


def test_CI_IN_02_claim_identifier_is_preserved_through_integration():
    """CI-IN-02 Inspection/Test: verify that the claim identifier is preserved from CI output through Integration."""
    ci = FakeCI()
    out = run(ci)
    sent = [q.claim_id for q in ci.seen]
    assert [r.claim_id for r in out.ci_results] == sent
    assert [r.findings[0].claim_id for r in out.ci_results] == sent
    assert [c["claim_id"] for c in out.model_dump(mode="json")["ci_results"]] == sent


def test_CI_IN_03_and_05_evidence_stays_with_its_own_claim(monkeypatch):
    """CI-IN-03 Inspection: verify that evidence references remain associated with the correct investigation result.
    CI-IN-05 Demonstration/Test: Integration can associate evidence with the correct claim result without ambiguity."""
    ci = FakeCI()
    out = run(ci)
    for r in out.ci_results:  # unchanged and still attached to its own claim (INT-8)
        assert r.findings[0].evidence == [evidence_for(next(q for q in ci.seen if q.claim_id == r.claim_id))]
    rows = claim_rows(page(FakeCI(), monkeypatch))
    assert len(rows) == len(out.ie.identified_claims) >= 2
    for claim, row in zip(out.ie.identified_claims, rows):  # each row shows its own evidence and no other claim's
        assert f"<code>{claim.claim_text}</code>" in row
        assert re.findall(r"src/evidence_for_([\w-]+)\.py", row) == [claim.claim_id], row


def test_CI_IN_04_reason_for_an_incomplete_check_is_transferred(monkeypatch):
    """CI-IN-04 Test: provide a claim that cannot be fully investigated and verify that the reason is transferred."""
    first = run(FakeCI()).ci_results[0].claim_id
    out = run(FakeCI(insufficient=[first]))
    r = next(r for r in out.ci_results if r.claim_id == first)
    assert r.limitation == "repository mirror unavailable"
    assert any("repository mirror unavailable" in line for line in out.could_not_check)
    assert "repository mirror unavailable" in page(FakeCI(insufficient=[first]), monkeypatch)


def test_CI_IN_06_insufficient_evidence_is_preserved_in_the_final_output(monkeypatch):
    """CI-IN-06 Test: verify that an insufficient-evidence or unable-to-check result is preserved in the final output."""
    first = run(FakeCI()).ci_results[0].claim_id
    out = run(FakeCI(insufficient=[first]))
    r = next(r for r in out.ci_results if r.claim_id == first)
    assert r.findings[0].outcome == "insufficient evidence" and r.findings[0].evidence == []
    assert any("insufficient evidence" in line for line in out.could_not_check)
    assert "Insufficient evidence" in page(FakeCI(insufficient=[first]), monkeypatch)


def test_5_3_feedback_when_a_result_cannot_be_connected_to_its_claim():
    """5.3: Integration gives feedback when an investigation result cannot be received or connected to the correct claim."""
    class WrongClaim(FakeCI):
        def investigate(self, request):
            return super().investigate(request.model_copy(update={"claim_id": "someone-else"}))

    out = run(WrongClaim())
    assert out.ci_results == []
    assert any("answered for another claim" in line for line in out.could_not_check)


def test_5_4_fields_beyond_the_current_draft_are_kept_unchanged():
    """The CI schema is still open (section 8), so extra fields CI adds are accepted and passed on unchanged."""
    out = run(FakeCI(extra={"checked_version": "v1.2.0"}))
    assert all(r.model_dump()["checked_version"] == "v1.2.0" for r in out.ci_results)

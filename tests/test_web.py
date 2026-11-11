"""Web interface: form, HTML result, JSON API, error handling."""
import pytest
from fastapi.testclient import TestClient

from bugs26.integration import github, pipeline
from bugs26.integration.models import Evidence, Finding, IEResult
from bugs26.web.app import app
from conftest import NAMES, sample

client = TestClient(app)


def test_index_has_form():
    r = client.get("/")
    assert r.status_code == 200 and "<textarea" in r.text and 'type="file"' in r.text and "issue_url" in r.text


def test_evaluate_html_result(good):
    r = client.post("/evaluate", data={"text": good, "repo_url": "https://github.com/o/r"})
    assert r.status_code == 200
    for s in ("Input Evaluation", "Claim Investigation", "Could not check", "PLACEHOLDER", "Download JSON",
              "Worth investigating", "Original report", "lines ", "Technical details"):
        assert s in r.text


def test_all_samples_via_both_endpoints():
    for name in NAMES:
        assert client.post("/evaluate", data={"text": sample(name)}).status_code == 200
        body = client.post("/api/evaluate", data={"text": sample(name)}).json()
        assert body["could_not_check"] and body["ie_decision"]


def test_xss_is_escaped_everywhere():
    evil = "<script>alert(1)</script>"
    body = f"# {evil}\n## Steps to reproduce\n{evil} in `{evil[:8]}()`\n## Expected\n{evil}\n## Actual\nx {evil}()"
    r = client.post("/evaluate", data={"text": body})
    assert evil not in r.text and "&lt;script&gt;" in r.text


def test_error_page_not_json():
    r = client.post("/evaluate", data={"text": "  "})
    assert r.status_code == 400 and "text/html" in r.headers["content-type"] and "exactly one" in r.text


def test_api_errors_are_json():
    r = client.post("/api/evaluate", data={"text": "  "})
    assert r.status_code == 400 and "detail" in r.json()


def test_bom_upload_is_decoded():
    data = b"\xef\xbb\xbf# Title here\n## Steps\nx"
    body = client.post("/api/evaluate", files={"file": ("a.md", data, "text/markdown")}).json()
    assert body["original_body"].startswith("# Title here") and body["structured"]["title"] is None
    assert body["source"] == "upload"


def test_empty_upload_is_ignored_when_pasting(good):
    r = client.post("/api/evaluate", data={"text": good}, files={"file": ("empty.md", b"", "text/markdown")})
    assert r.status_code == 200 and r.json()["source"] == "paste"


def test_paste_and_upload_together_is_rejected(good):
    r = client.post("/api/evaluate", data={"text": good}, files={"file": ("a.md", b"x", "text/markdown")})
    assert r.status_code == 400


def test_rejects_big_and_wrong_type():
    big = ("x" * (200 * 1024 + 1)).encode()
    assert client.post("/api/evaluate", files={"file": ("a.txt", big, "text/plain")}).status_code == 413
    assert client.post("/api/evaluate", files={"file": ("a.exe", b"hi", "text/plain")}).status_code == 400


def test_oversize_content_length_rejected_before_parsing():
    r = client.post("/evaluate", content=b"x", headers={"content-length": str(300 * 1024),
                                                       "content-type": "application/x-www-form-urlencoded"})
    assert r.status_code == 413


def test_github_issue_source(monkeypatch):
    monkeypatch.setattr(github, "_http_get", lambda u: {"title": "Boom", "body": "## Steps\nx",
                                                        "html_url": "https://github.com/o/r/issues/2"})
    body = client.post("/api/evaluate", data={"issue_url": "https://github.com/o/r/issues/2"}).json()
    assert body["source"] == "github" and body["original_title"] == "Boom" and body["issue_url"].endswith("/issues/2")
    r = client.post("/evaluate", data={"issue_url": "https://example.com/x"})
    assert r.status_code == 400 and "Not a GitHub issue URL" in r.text


def test_unsupported_repo_error_page(monkeypatch):
    monkeypatch.setattr(github, "_http_get", lambda u: pytest.fail("no network call expected"))
    r = client.post("/evaluate", data={"issue_url": "https://github.com/jqlang/jq/issues/3597"})
    assert r.status_code == 400 and "not a supported repository" in r.text and "supported_repos.txt" in r.text


def test_freeform_paste_maps_to_description():
    body = client.post("/api/evaluate", data={"text": "The app crashes when I click save."}).json()
    assert body["structured"]["fields"]["description"][0]["text"] == "The app crashes when I click save."
    assert any(f["subject"] == "C1 description" and f["status"] == "present" for f in body["findings"])


def test_result_page_ux(monkeypatch):
    issue = {"title": "<b>Boom</b>", "body": "## Steps\n1. go\n## Expected\n" + "x" * 500,
             "html_url": "https://github.com/o/r/issues/2"}
    monkeypatch.setattr(github, "_http_get", lambda u: issue)
    r = client.post("/evaluate", data={"issue_url": "https://github.com/o/r/issues/2"})
    assert "<h2>&lt;b&gt;Boom&lt;/b&gt;</h2>" in r.text
    assert 'href="https://github.com/o/r/issues/2"' in r.text
    findings_part = r.text.split("Findings</h2>")[1].split("Original report")[0]
    assert "report:" not in findings_part  # internal refs hidden
    assert "x" * 201 not in findings_part  # excerpt truncated; full text is in the original view
    assert "x" * 500 in r.text.split("Original report")[1]


def test_issue_link_only_for_github_urls(monkeypatch):
    issue = {"title": "T", "body": "## Steps\nx", "html_url": "javascript:alert(1)"}
    monkeypatch.setattr(github, "_http_get", lambda u: issue)
    r = client.post("/evaluate", data={"issue_url": "https://github.com/o/r/issues/2"})
    assert 'href="javascript:' not in r.text


def with_evaluator(monkeypatch, evaluator):
    real = pipeline.run
    monkeypatch.setattr("bugs26.web.app.pipeline.run", lambda *a, **k: real(*a, evaluator=evaluator, **k))


def test_lines_are_computed_when_ie_sends_only_spans(good, monkeypatch):
    class SpanOnlyIE:
        def evaluate(self, raw, structured):
            ev = Evidence(kind="report_excerpt", ref=f"report:{raw.report_id}", excerpt="x", start=0, end=5)
            f = Finding(finding_id="f", report_id=raw.report_id, source="input_evaluation", subject="s",
                        status="present", statement="s", evidence=[ev])
            return IEResult(report_id=raw.report_id, findings=[f])
    with_evaluator(monkeypatch, SpanOnlyIE())
    r = client.post("/evaluate", data={"text": good})
    assert 'href="#L1">lines 1&ndash;1</a>' in r.text


def test_ie_failure_is_an_error_page_not_a_500(good, monkeypatch):
    class Boom:
        def evaluate(self, raw, structured):
            raise RuntimeError("nope")
    with_evaluator(monkeypatch, Boom())
    r = client.post("/evaluate", data={"text": good})
    assert r.status_code == 400 and "Input Evaluation failed" in r.text

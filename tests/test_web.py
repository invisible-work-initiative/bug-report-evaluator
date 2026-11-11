"""Web interface: form, HTML result, JSON API, error handling."""
from fastapi.testclient import TestClient

from bugs26.integration import github
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
              "Decision: investigate", "Original report", "chars "):
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
    assert body["original_body"].startswith("# Title here") and body["structured"]["title"] == "Title here"
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

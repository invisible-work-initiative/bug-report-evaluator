"""Web interface: form, HTML result, JSON API, upload limits."""
from fastapi.testclient import TestClient

from bugs26.web.app import app
from conftest import sample

client = TestClient(app)


def test_index_has_form():
    r = client.get("/")
    assert r.status_code == 200 and "<textarea" in r.text and 'type="file"' in r.text


def test_evaluate_html_result(good):
    r = client.post("/evaluate", data={"text": good, "repo_url": "https://github.com/o/r"})
    assert r.status_code == 200
    assert "Input Evaluation" in r.text and "Claim Investigation" in r.text
    assert "Could not check" in r.text and "PLACEHOLDER" in r.text
    assert "Download JSON" in r.text


def test_excerpts_are_escaped():
    r = client.post("/evaluate", data={"text": "# <script>alert(1)</script>\n"})
    assert "<script>alert(1)</script>" not in r.text
    assert "&lt;script&gt;" in r.text


def test_api_json_with_upload():
    text = sample("cites-nonexistent-file.md")
    r = client.post("/api/evaluate", files={"file": ("bug.md", text.encode(), "text/markdown")})
    assert r.status_code == 200
    body = r.json()
    assert body["could_not_check"]
    assert any(f["source"] == "claim_investigation" for f in body["findings"])


def test_rejects_empty_big_and_wrong_type():
    assert client.post("/api/evaluate", data={"text": "  "}).status_code == 400
    big = ("x" * (200 * 1024 + 1)).encode()
    assert client.post("/api/evaluate", files={"file": ("a.txt", big, "text/plain")}).status_code == 413
    assert client.post("/api/evaluate", files={"file": ("a.exe", b"hi", "text/plain")}).status_code == 400

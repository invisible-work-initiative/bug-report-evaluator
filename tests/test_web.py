"""Web interface: form, HTML result, JSON API, error handling."""
import pytest
from fastapi.testclient import TestClient

from bugs26.integration import github, pipeline
from bugs26.web.app import app
from conftest import NAMES, ie_result, sample

client = TestClient(app)


def test_index_has_form():
    r = client.get("/")
    assert r.status_code == 200 and "<textarea" in r.text and 'type="file"' in r.text and "issue_url" in r.text


def test_evaluate_html_result(good):
    r = client.post("/evaluate", data={"text": good, "repo_url": "https://github.com/o/r"})
    assert r.status_code == 200
    for s in ("Input Evaluation", "Claim Investigation", "Could not check", "PLACEHOLDER", "Download JSON",
              "Partial evaluation", "Original report", "line ", "Technical details", "C7 Clarity and specificity",
              "are placeholders", "outside the current IE agreement, decision 0006", "Not investigated"):
        assert s in r.text


def test_all_samples_via_both_endpoints():
    for name in NAMES:
        assert client.post("/evaluate", data={"text": sample(name)}).status_code == 200
        body = client.post("/api/evaluate", data={"text": sample(name)}).json()
        assert body["could_not_check"] and body["ie"]["processing_status"]


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
    assert body["record"]["raw_body"].startswith("# Title here") and body["record"]["title"] == ""
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
    assert body["source"] == "github" and body["record"]["title"] == "Boom" and body["record"]["issue_url"].endswith("/issues/2") and body["record"]["issue_number"] == 2
    r = client.post("/evaluate", data={"issue_url": "https://example.com/x"})
    assert r.status_code == 400 and "Not a GitHub issue URL" in r.text


def test_unsupported_repo_error_page(monkeypatch):
    monkeypatch.setattr(github, "_http_get", lambda u: pytest.fail("no network call expected"))
    r = client.post("/evaluate", data={"issue_url": "https://github.com/jqlang/jq/issues/3597"})
    assert r.status_code == 400 and "This repository is not supported yet" in r.text and "supported_repos.txt" not in r.text


def test_freeform_paste_has_no_sections():
    body = client.post("/api/evaluate", data={"text": "The app crashes when I click save."}).json()
    assert body["record"]["sections"] == [] and body["record"]["extraction"]["mode"] == "free_form"
    assert body["ie"]["processing_status"] == "partial" and body["ie"]["unevaluated_criteria"][0] == "C1"


def test_result_page_ux(monkeypatch):
    issue = {"title": "<b>Boom</b>", "body": "## Steps\n1. go\n## Expected\n" + "x" * 500,
             "html_url": "https://github.com/o/r/issues/2"}
    monkeypatch.setattr(github, "_http_get", lambda u: issue)
    r = client.post("/evaluate", data={"issue_url": "https://github.com/o/r/issues/2"})
    assert "<h2>&lt;b&gt;Boom&lt;/b&gt;</h2>" in r.text
    assert 'href="https://github.com/o/r/issues/2"' in r.text
    findings_part = r.text.split("Input Evaluation</h2>")[1].split("Original report")[0]
    assert "x" * 201 not in findings_part  # quote truncated; full text is in the original view
    assert "x" * 500 in r.text.split("Original report")[1]


def test_issue_link_only_for_github_urls(monkeypatch):
    issue = {"title": "T", "body": "## Steps\nx", "html_url": "javascript:alert(1)"}
    monkeypatch.setattr(github, "_http_get", lambda u: issue)
    r = client.post("/evaluate", data={"issue_url": "https://github.com/o/r/issues/2"})
    assert 'href="javascript:' not in r.text


def with_evaluator(monkeypatch, evaluator):
    real = pipeline.run
    monkeypatch.setattr("bugs26.web.app.pipeline.run", lambda *a, **k: real(*a, evaluator=evaluator, **k))


def test_ie_evidence_lines_link_to_the_original(good, monkeypatch):
    with_evaluator(monkeypatch, PlainIE())
    r = client.post("/evaluate", data={"text": good})
    assert 'href="#L3">lines 3&ndash;4</a>' in r.text and '<tr id="L3">' in r.text


class PlainIE:
    def evaluate(self, record):
        from bugs26.integration.models import IELines
        from conftest import ie_evidence
        res = ie_result(record)
        res.criterion_findings[0].evidence[:] = [ie_evidence("x", basis="quotation", source="raw_body",
                                                             lines=IELines(start=3, end=4), quote="q")]
        return res


def test_ie_failure_is_an_error_page_not_a_500(good, monkeypatch):
    class Boom:
        def evaluate(self, raw, structured):
            raise RuntimeError("nope")
    with_evaluator(monkeypatch, Boom())
    r = client.post("/evaluate", data={"text": good})
    assert r.status_code == 502 and "Input Evaluation failed" in r.text


def test_short_keeps_line_endings_and_adds_dots_only_when_cut():
    from bugs26.web.app import short
    assert short("a\r\nb\r\nc") == "a\r\nb\r\nc"          # nothing cut, no dots
    assert short("a\nb\nc\n") == "a\nb\nc\n"
    assert short("a\r\nb\nc\nd") == "a\r\nb\nc\n..."      # 4th line cut, endings kept
    assert short("x" * 201) == "x" * 200 + "..." and short(None) == ""


def test_repo_url_is_validated_for_paste():
    ok = client.post("/api/evaluate", data={"text": "bug", "repo_url": "https://github.com/o/r"})
    assert ok.status_code == 200 and client.post("/api/evaluate", data={"text": "bug"}).status_code == 200
    for bad in ("https://evil.example/o/r", "https://github.com/jqlang/jq", "javascript:alert(1)", "o/r"):
        r = client.post("/api/evaluate", data={"text": "bug", "repo_url": bad})
        assert r.status_code == 400, bad


def test_summary_banner_and_tables(good):
    r = client.post("/evaluate", data={"text": good})
    assert "Partial evaluation" in r.text and "Claims: 3 identified, 0 investigated" in r.text
    assert "Present 5" in r.text and "not evaluated 2" in r.text
    assert "A bug description section is present" in r.text and "Not evaluated" in r.text and "A expected" not in r.text
    assert "An expected behavior section is present" in r.text and r.text.count("Partial evaluation") == 1
    assert "<code>src/mytool/config.py:88</code>" in r.text and "Not investigated" in r.text


def test_unmapped_sections_are_not_a_maintainer_gap():
    r = client.post("/api/evaluate", data={"text": "## Foo\na\n## Bar\nb\n## Steps\nc"}).json()
    assert not any("Foo" in c for c in r["could_not_check"])
    assert [(s["original_label"], s["recognition"]) for s in r["record"]["sections"]] == [
        ("Foo", "unrecognized"), ("Bar", "unrecognized"), ("Steps", "recognized")]


def test_missing_heading_is_not_called_missing_information(good):
    r = client.post("/api/evaluate", data={"text": "## Expected\nok"}).json()
    c2 = r["ie"]["criterion_findings"][1]
    assert (c2["rating"], c2["evaluation_status"]) == (None, "unevaluated")  # the stub never says M
    assert all(f["rating"] != "M" for f in r["ie"]["criterion_findings"])


def test_missing_or_insufficient_label_for_m(monkeypatch):
    class MIE:
        def evaluate(self, record):
            res = ie_result(record)
            res.criterion_findings[1] = res.criterion_findings[1].model_copy(update={"rating": "M"})
            return res
    with_evaluator(monkeypatch, MIE())
    assert "Missing or insufficient (M)" in client.post("/evaluate", data={"text": "x"}).text


def test_offline_demo_sample_lists_claims_as_not_investigated():
    body = client.post("/api/evaluate", data={"text": sample("issue-form-report.md")}).json()
    assert body["ie"]["processing_status"] == "partial" and len(body["ie"]["identified_claims"]) == 5
    assert body["ci_results"] == []  # the CI stub invents no outcome
    assert sum("not investigated: NotImplementedError" in c for c in body["could_not_check"]) == 5
    assert [c for c in body["could_not_check"] if c.startswith("C")][:2] == [
        "C6 not evaluated (dependency_unavailable): C6: The placeholder does not judge this criterion.",
        "C7 not evaluated (dependency_unavailable): C7: The placeholder does not judge this criterion."]


def test_no_checkable_claims_is_shown():
    r = client.post("/evaluate", data={"text": "## Steps\nit just breaks"})
    assert "No claims were identified." in r.text and "was not called" in r.text

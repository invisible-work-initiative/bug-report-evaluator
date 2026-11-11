"""INT-1 Verification: submit a sample GitHub bug report and check that Integration receives it."""
import hashlib
from pathlib import Path

import pytest

from bugs26.integration import github, intake
from bugs26.integration.models import RawReport

ISSUE = {"title": "Crash on start", "body": "## Steps to reproduce\nrun it", "html_url": "https://github.com/o/r/issues/7",
         "number": 7, "created_at": "2026-11-01T14:00:00Z", "updated_at": "2026-11-02T09:30:00Z",
         "user": {"login": "someone"}, "assignee": {"login": "x"}, "labels": [{"name": "bug", "id": 5}]}


def test_sample_report_is_received_verbatim(good):
    raw = intake.receive(good, "upload", "https://github.com/o/r")
    assert raw.raw_body == good and raw.title == ""
    assert raw.sha256 == hashlib.sha256(("\n" + good).encode()).hexdigest()
    assert raw.report_id and raw.source == "upload" and raw.repository == "o/r"
    # not a GitHub issue: nothing is made up (IE open question Q3); body_source is always "current"
    assert (raw.issue_number, raw.issue_url, raw.created_at, raw.updated_at) == (None, None, None, None)
    assert raw.body_source == "current" and raw.labels == []


def test_crlf_is_kept_and_title_is_hashed():
    raw = intake.receive("a\r\nb", "paste", title="T")
    assert raw.raw_body == "a\r\nb"
    assert raw.sha256 == hashlib.sha256(b"T\na\r\nb").hexdigest()


def test_each_submission_gets_its_own_ids(good):
    a, b = intake.receive(good, "paste"), intake.receive(good, "paste")
    assert len({a.report_id, b.report_id, a.request_id, b.request_id, a.snapshot_id, b.snapshot_id}) == 6


def test_empty_body_is_valid():
    """IE draft: raw_body "" is allowed (GitHub's null body is sent as "")."""
    raw = intake.receive("", "github", "https://github.com/o/r", "T", issue_number=3)
    assert raw.raw_body == "" and raw.title == "T"
    assert intake.structure(raw).sections == []


def test_github_issue_is_fetched(monkeypatch):
    urls = []
    monkeypatch.setattr(github, "_http_get", lambda u: urls.append(u) or ISSUE)
    got = github.fetch_issue("https://github.com/o/r/issues/7")
    assert urls == ["https://api.github.com/repos/o/r/issues/7"]
    assert got == {"title": "Crash on start", "body": ISSUE["body"], "issue_url": "https://github.com/o/r/issues/7",
                   "repo_url": "https://github.com/o/r", "issue_number": 7, "labels": ["bug"],
                   "created_at": "2026-11-01T14:00:00Z", "updated_at": "2026-11-02T09:30:00Z"}  # no user, assignee


def test_null_body_becomes_empty_string(monkeypatch):
    monkeypatch.setattr(github, "_http_get", lambda u: {**ISSUE, "body": None})
    assert github.fetch_issue("https://github.com/o/r/issues/7")["body"] == ""


def test_pull_request_is_rejected(monkeypatch):
    monkeypatch.setattr(github, "_http_get", lambda u: {**ISSUE, "pull_request": {}})
    with pytest.raises(github.GitHubError, match="pull request"):
        github.fetch_issue("https://github.com/o/r/issues/7")


@pytest.mark.parametrize("url", ["https://example.com/o/r/issues/1", "https://github.com/o/r/pull/1",
                                 "https://github.com/o/r/issues/x", "not a url",
                                 "https://github.com/../r/issues/1", "https://github.com/o/../issues/1",
                                 "https://github.com/o/r/issues/1\n/x", "https://github.com/ö/r/issues/1",
                                 "https://github.com/o/r/issues/١٢", "https://github.com/o/r/issues/1?x=1"])
def test_bad_url_is_rejected(monkeypatch, url):
    monkeypatch.setattr(github, "_http_get", lambda u: pytest.fail("no network call expected"))
    with pytest.raises(github.GitHubError):
        github.fetch_issue(url)


def test_received_github_report_has_no_author(monkeypatch):
    monkeypatch.setattr(github, "_http_get", lambda u: ISSUE)
    got = github.fetch_issue("https://github.com/o/r/issues/7")
    raw = intake.receive(got["body"], "github", got["repo_url"], got["title"], got["issue_url"],
                         issue_number=got["issue_number"], labels=got["labels"], created_at=got["created_at"],
                         updated_at=got["updated_at"])
    assert "someone" not in raw.model_dump_json()
    assert (raw.repository, raw.issue_number, raw.labels, raw.created_at) == ("o/r", 7, ["bug"], "2026-11-01T14:00:00Z")
    assert "user" not in RawReport.model_fields and "author" not in RawReport.model_fields


@pytest.mark.parametrize("url, ok", [("https://github.com/o/r", True), ("https://github.com/O/R/", True),
                                     ("https://github.com/o/r/issues/1", False), ("https://github.com/jqlang/jq", False),
                                     ("http://github.com/o/r", False), ("https://github.com/../r", False), ("o/r", False)])
def test_repo_url_parse(url, ok):
    if ok:
        assert github.parse(url, issue=False)[:2] in {("o", "r"), ("O", "R")}
    else:
        with pytest.raises(github.GitHubError):
            github.parse(url, issue=False)


def test_oserror_from_github_is_a_clean_error(monkeypatch):
    def boom(*a, **k):
        raise ConnectionResetError("reset")
    monkeypatch.setattr(github.urllib.request, "urlopen", boom)
    with pytest.raises(github.GitHubError, match="Could not get this issue"):
        github.fetch_issue("https://github.com/o/r/issues/1")


def test_non_object_answer_is_rejected(monkeypatch):
    monkeypatch.setattr(github, "_http_get", lambda u: ["not", "a", "dict"])
    with pytest.raises(github.GitHubError):
        github.fetch_issue("https://github.com/o/r/issues/7")


def test_unsupported_repo_gives_a_maintainer_message(monkeypatch):
    monkeypatch.setattr(github, "_http_get", lambda u: pytest.fail("no network call expected"))
    with pytest.raises(github.GitHubError, match="This repository is not supported yet"):
        github.fetch_issue("https://github.com/jqlang/jq/issues/3597")


def test_supported_repos_file_is_case_insensitive(tmp_path, monkeypatch):
    real = Path(github.__file__).with_name("supported_repos.txt")
    monkeypatch.setattr(github, "SUPPORTED_FILE", real)
    assert {"psf/requests", "pandas-dev/pandas", "kubernetes/kubernetes", "grafana/grafana", "obsproject/obs-studio",
            "ansible/ansible", "docker/compose", "ollama/ollama"} <= github.supported_repos()
    monkeypatch.setattr(github, "_http_get", lambda u: ISSUE)
    assert github.fetch_issue("https://github.com/PSF/Requests/issues/1")["repo_url"] == "https://github.com/PSF/Requests"

"""INT-1 Verification: submit a sample GitHub bug report and check that Integration receives it."""
import hashlib
from pathlib import Path

import pytest

from bugs26.integration import github, intake
from bugs26.integration.models import RawReport

ISSUE = {"title": "Crash on start", "body": "## Steps to reproduce\nrun it", "html_url": "https://github.com/o/r/issues/7",
         "user": {"login": "someone"}, "assignee": {"login": "x"}, "labels": [{"name": "bug"}]}


def test_sample_report_is_received_verbatim(good):
    raw = intake.receive(good, "upload", "https://github.com/o/r")
    assert raw.original_body == good and raw.original_title is None
    assert raw.sha256 == hashlib.sha256(("\n" + good).encode()).hexdigest()
    assert raw.report_id and raw.source == "upload" and raw.repo_url == "https://github.com/o/r"


def test_crlf_is_kept_and_title_is_hashed():
    raw = intake.receive("a\r\nb", "paste", title="T")
    assert raw.original_body == "a\r\nb"
    assert raw.sha256 == hashlib.sha256(b"T\na\r\nb").hexdigest()


def test_each_submission_gets_its_own_id(good):
    assert intake.receive(good, "paste").report_id != intake.receive(good, "paste").report_id


def test_empty_body_is_refused():
    with pytest.raises(intake.PreparationError):
        intake.receive("  \n", "paste")


def test_github_issue_is_fetched(monkeypatch):
    urls = []
    monkeypatch.setattr(github, "_http_get", lambda u: urls.append(u) or ISSUE)
    got = github.fetch_issue("https://github.com/o/r/issues/7")
    assert urls == ["https://api.github.com/repos/o/r/issues/7"]
    assert got == {"title": "Crash on start", "body": ISSUE["body"], "issue_url": "https://github.com/o/r/issues/7",
                   "repo_url": "https://github.com/o/r"}  # no user, labels, assignee


def test_pull_request_is_rejected(monkeypatch):
    monkeypatch.setattr(github, "_http_get", lambda u: {**ISSUE, "pull_request": {}})
    with pytest.raises(github.GitHubError, match="pull request"):
        github.fetch_issue("https://github.com/o/r/issues/7")


@pytest.mark.parametrize("url", ["https://example.com/o/r/issues/1", "https://github.com/o/r/pull/1",
                                 "https://github.com/o/r/issues/x", "not a url",
                                 "https://github.com/../r/issues/1", "https://github.com/o/../issues/1",
                                 "https://github.com/o/r/issues/1\n/x", "https://github.com/\u00f6/r/issues/1",
                                 "https://github.com/o/r/issues/\u0661\u0662", "https://github.com/o/r/issues/1?x=1"])
def test_bad_url_is_rejected(monkeypatch, url):
    monkeypatch.setattr(github, "_http_get", lambda u: pytest.fail("no network call expected"))
    with pytest.raises(github.GitHubError):
        github.fetch_issue(url)


def test_received_github_report_has_no_author(monkeypatch):
    monkeypatch.setattr(github, "_http_get", lambda u: ISSUE)
    got = github.fetch_issue("https://github.com/o/r/issues/7")
    raw = intake.receive(got["body"], "github", got["repo_url"], got["title"], got["issue_url"])
    assert "someone" not in raw.model_dump_json()
    assert "user" not in RawReport.model_fields and "author" not in RawReport.model_fields


def test_non_object_answer_is_rejected(monkeypatch):
    monkeypatch.setattr(github, "_http_get", lambda u: ["not", "a", "dict"])
    with pytest.raises(github.GitHubError):
        github.fetch_issue("https://github.com/o/r/issues/7")


def test_unsupported_repo_gives_a_clear_error(monkeypatch):
    monkeypatch.setattr(github, "_http_get", lambda u: pytest.fail("no network call expected"))
    with pytest.raises(github.GitHubError, match="not a supported repository.*supported_repos.txt"):
        github.fetch_issue("https://github.com/jqlang/jq/issues/3597")


def test_supported_repos_file_is_case_insensitive(tmp_path, monkeypatch):
    real = Path(github.__file__).with_name("supported_repos.txt")
    monkeypatch.setattr(github, "SUPPORTED_FILE", real)
    assert {"psf/requests", "pandas-dev/pandas", "kubernetes/kubernetes", "grafana/grafana", "obsproject/obs-studio",
            "ansible/ansible", "docker/compose", "ollama/ollama"} <= github.supported_repos()
    monkeypatch.setattr(github, "_http_get", lambda u: ISSUE)
    assert github.fetch_issue("https://github.com/PSF/Requests/issues/1")["repo_url"] == "https://github.com/PSF/Requests"

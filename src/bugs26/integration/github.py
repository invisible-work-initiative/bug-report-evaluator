"""INT-1: fetch one public GitHub issue (stdlib only). Keeps title, body, URL, number, label names and timestamps - no person (INT-9)."""
import json
import os
import re
import urllib.request
from pathlib import Path

_URL = re.compile(r"https://github\.com/(?P<owner>[\w.-]+)/(?P<repo>[\w.-]+)(?:/issues/(?P<number>\d+))?/?", re.ASCII)
SUPPORTED_FILE = Path(__file__).with_name("supported_repos.txt")


class GitHubError(ValueError):
    """The issue could not be fetched or is not a plain issue."""


def _http_get(url: str) -> dict:
    """The only network call. Tests replace this function."""
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "bugs26-prototype"}
    if os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = "Bearer " + os.environ["GITHUB_TOKEN"]
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (OSError, ValueError) as e:  # URLError, HTTPError and timeouts are OSErrors
        raise GitHubError(f"Could not get this issue from GitHub ({getattr(e, 'code', type(e).__name__)}).") from None


def supported_repos() -> set[str]:
    """INT-1: the repositories we accept, lower case, from supported_repos.txt."""
    lines = (l.strip().lower() for l in SUPPORTED_FILE.read_text(encoding="utf-8").splitlines())
    return {l for l in lines if l and not l.startswith("#")}


def parse(url: str, issue: bool):
    """(owner, repo, number) of a GitHub repo or issue URL; the repo must be in supported_repos.txt."""
    m = _URL.fullmatch(url.strip())
    if not m or bool(m.group("number")) != issue or {m.group("owner"), m.group("repo")} & {".", ".."}:
        raise GitHubError("Not a GitHub issue URL. Expected https://github.com/OWNER/REPO/issues/NUMBER." if issue
                          else "Repository URL must look like https://github.com/OWNER/REPO.")
    owner, repo = m.group("owner", "repo")
    if f"{owner}/{repo}".lower() not in supported_repos():
        raise GitHubError(f"This repository is not supported yet ({owner}/{repo}).")
    return owner, repo, m.group("number")


def fetch_issue(issue_url: str) -> dict:
    """Return title, body, issue_url, repo_url, issue_number, labels (names), created_at, updated_at for https://github.com/{o}/{r}/issues/{n}."""
    owner, repo, number = parse(issue_url, issue=True)
    data = _http_get(f"https://api.github.com/repos/{owner}/{repo}/issues/{number}")
    if not isinstance(data, dict):
        raise GitHubError("Unexpected answer from GitHub.")
    if "pull_request" in data:
        raise GitHubError("This URL is a pull request, not a bug report issue.")
    return {
        "title": data.get("title"),
        "body": data.get("body") or "",
        "issue_url": data.get("html_url") or issue_url.strip(),
        "repo_url": f"https://github.com/{owner}/{repo}",
        "issue_number": int(number),
        "labels": [l["name"] for l in data.get("labels") or [] if isinstance(l, dict) and isinstance(l.get("name"), str)],
        "created_at": data.get("created_at"),
        "updated_at": data.get("updated_at"),
    }

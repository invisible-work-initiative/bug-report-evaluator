"""INT-1: fetch one public GitHub issue (stdlib only). Keeps title, body and html_url - nothing else (INT-9)."""
import json
import os
import re
import urllib.error
import urllib.request

_ISSUE_URL = re.compile(r"^https://github\.com/(?P<owner>[\w.-]+)/(?P<repo>[\w.-]+)/issues/(?P<number>\d+)/?", re.ASCII)


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
    except urllib.error.HTTPError as e:
        raise GitHubError(f"GitHub returned HTTP {e.code} for this issue.") from None
    except (urllib.error.URLError, TimeoutError, ValueError):
        raise GitHubError("Could not reach GitHub.") from None


def fetch_issue(issue_url: str) -> dict:
    """Return {"title", "body", "issue_url", "repo_url"} for https://github.com/{o}/{r}/issues/{n}."""
    m = _ISSUE_URL.fullmatch(issue_url.strip())
    if not m or {m.group("owner"), m.group("repo")} & {".", ".."}:
        raise GitHubError("Not a GitHub issue URL. Expected https://github.com/OWNER/REPO/issues/NUMBER.")
    owner, repo, number = m.group("owner", "repo", "number")
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
    }

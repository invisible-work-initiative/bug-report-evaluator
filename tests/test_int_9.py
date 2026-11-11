"""INT-9 Verification (inspection, automated): stored data and logs do not link a reporter across submissions."""
import re
from pathlib import Path

from bugs26.integration import github, models, pipeline
from bugs26.web import __main__ as runner

SRC = Path(models.__file__).resolve().parents[1]
IDENTITY = re.compile(r"author|reporter|user|username|login|email|ip_addr|assignee", re.I)


def all_models():
    return [c for c in vars(models).values() if isinstance(c, type) and issubclass(c, models.BaseModel)
            and c is not models.BaseModel]


def test_no_model_has_an_identity_field():
    assert len(all_models()) >= 9
    for cls in all_models():
        for name in cls.model_fields:
            assert not IDENTITY.search(name), f"{cls.__name__}.{name}"


def test_output_has_no_identity_keys(good):
    out = pipeline.run(good, "paste").model_dump(mode="json")

    def keys(x):
        if isinstance(x, dict):
            for k, v in x.items():
                yield k
                yield from keys(v)
        elif isinstance(x, list):
            for i in x:
                yield from keys(i)
    assert not [k for k in keys(out) if IDENTITY.search(k)]


def test_github_user_never_reaches_a_model(monkeypatch):
    payload = {"title": "T", "body": "## Steps\nx", "html_url": "https://github.com/o/r/issues/1",
               "user": {"login": "SECRETNAME"}, "assignees": [{"login": "SECRETNAME"}]}
    monkeypatch.setattr(github, "_http_get", lambda u: payload)
    got = github.fetch_issue("https://github.com/o/r/issues/1")
    out = pipeline.run(got["body"], "github", got["repo_url"], title=got["title"], issue_url=got["issue_url"],
                       issue_number=got["issue_number"], labels=got["labels"], created_at=got["created_at"],
                       updated_at=got["updated_at"])
    assert "SECRETNAME" not in out.model_dump_json() and "SECRETNAME" not in str(got)


def test_two_submissions_share_no_identifier(good):
    a, b = pipeline.run(good, "paste"), pipeline.run(good, "paste")
    ids_a = {a.record.request_id, a.record.snapshot_id}
    ids_b = {b.record.request_id, b.record.snapshot_id}
    assert not ids_a & ids_b


def test_runner_turns_access_log_off(monkeypatch):
    seen = {}
    monkeypatch.setattr(runner.uvicorn, "run", lambda *a, **kw: seen.update(kw))
    runner.main()
    assert seen["access_log"] is False


def test_code_neither_logs_nor_writes_files():
    for py in SRC.rglob("*.py"):
        code = py.read_text(encoding="utf-8")
        assert "import logging" not in code and "print(" not in code, py
        assert not re.search(r"\bopen\(|write_text|write_bytes|sqlite|shelve|pickle", code), py

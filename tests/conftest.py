from pathlib import Path

import pytest

SAMPLES = Path(__file__).resolve().parent.parent / "samples"
NAMES = ["good-report.md", "missing-steps.md", "cites-nonexistent-file.md"]


def sample(name: str) -> str:
    return (SAMPLES / name).read_text(encoding="utf-8")


@pytest.fixture
def good():
    return sample("good-report.md")


@pytest.fixture(autouse=True)
def supported_repo_o_r(tmp_path, monkeypatch):
    """Tests use the repo o/r; the real supported_repos.txt is tested separately."""
    from bugs26.integration import github
    f = tmp_path / "supported_repos.txt"
    f.write_text("# test list\no/r\n", encoding="utf-8")
    monkeypatch.setattr(github, "SUPPORTED_FILE", f)

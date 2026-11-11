from pathlib import Path

import pytest

SAMPLES = Path(__file__).resolve().parent.parent / "samples"


def sample(name: str) -> str:
    return (SAMPLES / name).read_text(encoding="utf-8")


@pytest.fixture
def good():
    return sample("good-report.md")

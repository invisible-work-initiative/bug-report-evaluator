"""INT-2 Verification: compare the original with the structured version; nothing lost or added."""
import pytest

from bugs26.integration import intake
from conftest import sample

NAMES = ["good-report.md", "missing-steps.md", "cites-nonexistent-file.md"]


def _strings(s):
    out = [v for k, v in s if isinstance(v, str) and k != "report_id"]
    out += [i for k, v in s if isinstance(v, list) for i in v]
    return out


@pytest.mark.parametrize("name", NAMES)
def test_nothing_added(name):
    raw = intake.receive(sample(name), "upload")
    structured = intake.structure(raw)
    for value in _strings(structured):
        assert value in raw.original_text


@pytest.mark.parametrize("name", NAMES)
def test_nothing_lost_and_original_untouched(name):
    text = sample(name)
    raw = intake.receive(text, "upload")
    s = intake.structure(raw)
    assert raw.original_text == text
    # every section the report has is captured
    for field in ("steps_to_reproduce", "expected_behavior", "observed_behavior", "environment"):
        has = {"steps_to_reproduce": "teps", "expected_behavior": "xpected",
               "observed_behavior": "ctual|bserved", "environment": "nvironment|Version"}[field]
        if any(h in text for h in has.split("|")):
            assert getattr(s, field), field


def test_good_report_fields(good):
    s = intake.structure(intake.receive(good, "paste"))
    assert s.title == "Crash when parsing empty config file"
    assert s.steps_to_reproduce.startswith("1. Run `touch config.yaml`")
    assert s.expected_behavior.startswith("The tool prints a warning")
    assert "src/mytool/config.py:88" in s.code_references
    assert "load_config()" in s.code_references
    assert "2.4.1" in "".join(s.versions)


def test_missing_sections_are_none_not_invented():
    s = intake.structure(intake.receive(sample("missing-steps.md"), "paste"))
    assert s.steps_to_reproduce is None
    assert s.title == "Export to PDF is broken"
    assert s.expected_behavior == "The exported PDF contains all pages of the document."
    assert s.observed_behavior.startswith("Only the first page")
    assert s.environment.startswith("1.8.0")
    assert s.code_references == []


def test_bare_text_has_only_a_title():
    s = intake.structure(intake.receive("it is broken", "paste"))
    assert s.title == "it is broken"
    assert s.steps_to_reproduce is s.expected_behavior is s.observed_behavior is s.environment is None

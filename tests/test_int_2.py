"""INT-2 Verification: compare the original with the structured version; nothing lost or added."""
import pytest

from bugs26.integration import intake
from conftest import NAMES, sample


def structured(body, title=None):
    raw = intake.receive(body, "paste", title=title)
    s = intake.structure(raw)
    intake.verify_structured(raw, s)
    return raw, s


def texts(s):
    return {f: [x.text for x in secs] for f, secs in s.fields.items()}


@pytest.mark.parametrize("name", NAMES)
def test_span_invariant_on_samples(name):
    raw, s = structured(sample(name))
    for sec in [x for v in s.fields.values() for x in v] + s.unmapped + s.code_references + s.versions:
        assert raw.original_body[sec.start:sec.end] == sec.text
    assert raw.original_body == sample(name)


@pytest.mark.parametrize("name", NAMES)
def test_nothing_lost_every_non_marker_char_is_in_a_section(name):
    """Removing all section texts from the body leaves only heading/label markup and whitespace."""
    raw, s = structured(sample(name))
    rest = raw.original_body
    for sec in sorted([x for v in s.fields.values() for x in v] + s.unmapped, key=lambda x: -x.start):
        rest = rest[:sec.start] + rest[sec.end:]
    assert all(l.strip().startswith(("#", "**")) or not l.strip() for l in rest.splitlines())


def test_good_report():
    _, s = structured(sample("good-report.md"))
    assert s.title == "Crash when parsing empty config file"
    assert list(texts(s)) == ["description", "steps_to_reproduce", "expected_behavior",
                              "observed_behavior", "environment"]
    assert texts(s)["steps_to_reproduce"][0].startswith("1. Run `touch config.yaml`")
    refs = [r.text for r in s.code_references]
    assert "src/mytool/config.py:88" in refs and "load_config()" in refs
    assert "v2.4.1" in [v.text for v in s.versions]


def test_missing_steps_sample():
    _, s = structured(sample("missing-steps.md"))
    assert s.title == "Export to PDF is broken" or s.title is None
    assert "steps_to_reproduce" not in s.fields
    assert texts(s)["expected_behavior"] == ["The exported PDF contains all pages of the document."]
    assert texts(s)["observed_behavior"][0].startswith("Only the first page")
    assert texts(s)["environment"][0].startswith("1.8.0 on macOS 14")
    assert s.code_references == []


CASES = {
    "bold note mid-steps stays in steps": (
        "## Steps to reproduce\n1. a\n**Note:** flaky\n2. b\n## Expected\nok",
        {"steps_to_reproduce": ["1. a\n**Note:** flaky\n2. b"], "expected_behavior": ["ok"]}, None),
    "heading inside fenced code is content": (
        "## Steps\n```\n# Expected\nfoo\n```\n## Expected behavior\nok",
        {"steps_to_reproduce": ["```\n# Expected\nfoo\n```"], "expected_behavior": ["ok"]}, None),
    "tilde fence": (
        "## Steps\n~~~\n## Expected\n~~~\n## Expected\nok",
        {"steps_to_reproduce": ["~~~\n## Expected\n~~~"], "expected_behavior": ["ok"]}, None),
    "system startup is not environment": (
        "# Crash on system startup\nIt crashes.", {}, "Crash on system startup"),
    "Conversion fails is a title, not a section": (
        "# Conversion fails\nIt fails.", {}, "Conversion fails"),
    "startup and versioning headings are unknown": (
        "intro\n## Startup\nx\n## Versioning notes\ny", {}, None),
    "repeated sections are all kept": (
        "## Steps\na\n## Steps\nb", {"steps_to_reproduce": ["a", "b"]}, None),
    "CRLF kept exactly": (
        "## Steps to reproduce\r\n1. a\r\n\r\n## Expected\r\nx\r\n",
        {"steps_to_reproduce": ["1. a"], "expected_behavior": ["x"]}, None),
    "bold labels with inline text": (
        "**Expected:** it works\n**Actual:** nope",
        {"expected_behavior": ["it works"], "observed_behavior": ["nope"]}, None),
    "unicode and emoji": (
        "## Steps to reproduce ✅\nÜber café\n## \U0001f41b Expected behavior\nnaïve",
        {"steps_to_reproduce": ["Über café"], "expected_behavior": ["naïve"]}, None),
    "one-liner": ("it is broken", {}, None),
    "alias as whole-word prefix": (
        "## Steps to reproduce the issue\nx", {"steps_to_reproduce": ["x"]}, None),
    "what happened instead beats what happened": (
        "## What happened instead\nboom", {"observed_behavior": ["boom"]}, None),
    "explicit title wins": ("## Steps\nx", {"steps_to_reproduce": ["x"]}, None),
}


@pytest.mark.parametrize("case", CASES)
def test_adversarial_cases(case):
    body, expected, title = CASES[case]
    given = "Given" if case == "explicit title wins" else None
    _, s = structured(body, title=given)
    assert texts(s) == expected
    assert s.title == (given or title)


def test_unmapped_sections():
    _, s = structured("Hello there\n## Screenshots\nimg\n## Steps\nx")
    assert [(u.label, u.text) for u in s.unmapped] == [(None, "Hello there"), ("Screenshots", "img")]
    _, s = structured("it is broken")
    assert [(u.label, u.text) for u in s.unmapped] == [(None, "it is broken")] and s.title is None
    _, s = structured("# Conversion fails\nIt fails.")
    assert [(u.label, u.text) for u in s.unmapped] == [(None, "It fails.")]


def test_github_default_template():
    body = ("**Describe the bug**\nA clear description.\n\n**To Reproduce**\nSteps to reproduce the behavior:\n1. Go\n\n"
            "**Expected behavior**\nIt works.\n\n**Desktop (please complete the following information):**\n"
            " - OS: iOS\n - Version 22\n")
    _, s = structured(body, title="Bug")
    t = texts(s)
    assert t["description"] == ["A clear description."]
    assert t["steps_to_reproduce"] == ["Steps to reproduce the behavior:\n1. Go"]
    assert t["expected_behavior"] == ["It works."]
    assert t["environment"] == ["- OS: iOS\n - Version 22"]
    assert s.title == "Bug"


def test_regex_fixes():
    _, s = structured("IP 192.168.1.1, v1.2.3 and 4.5.6.\nsee https://github.com/o/r/blob/main/a/b.py and src/b.py "
                      "and `foo()` and bar()")
    assert [v.text for v in s.versions] == ["v1.2.3", "4.5.6"]
    assert [r.text for r in s.code_references] == ["src/b.py", "foo()", "bar()"]


def test_verify_catches_a_wrong_span():
    raw, s = structured("## Steps\nabc")
    s.fields["steps_to_reproduce"][0].text = "abd"
    with pytest.raises(intake.PreparationError):
        intake.verify_structured(raw, s)

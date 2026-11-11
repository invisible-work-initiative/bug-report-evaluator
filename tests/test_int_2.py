"""INT-2 Verification: compare the original with the structured version; nothing lost or added."""
import pytest

from bugs26.integration import intake
from bugs26.integration.models import Section
from conftest import NAMES, sample


def structured(body, title=None):
    raw = intake.receive(body, "paste", title=title)
    s = intake.structure(raw)
    intake.verify_structured(raw, s)
    return raw, s


def texts(s):
    return {f: [x.text for x in secs] for f, secs in s.fields.items()}


def all_sections(s):
    return [x for v in s.fields.values() for x in v] + s.unmapped


def assert_nothing_lost(raw, s):
    """Cut every section text out of the body: what is left may only be marker lines (heading or
    bold label) whose label is the label of a section, plus whitespace. Heading lines are not exempt."""
    labels = {x.label for x in all_sections(s) if x.label}
    rest = raw.original_body
    for sec in sorted(all_sections(s), key=lambda x: -x.start):
        rest = rest[:sec.start] + rest[sec.end:]
    for line in rest.splitlines():
        label = line.strip().lstrip("#").strip().strip("*: \t").strip()
        assert not label or label in labels, f"lost text: {line!r}"


@pytest.mark.parametrize("name", NAMES)
def test_span_invariant_on_samples(name):
    raw, s = structured(sample(name))
    for sec in all_sections(s) + s.code_references + s.versions:
        assert raw.original_body[sec.start:sec.end] == sec.text
    assert raw.original_body == sample(name)
    assert_nothing_lost(raw, s)


def test_good_report():
    _, s = structured(sample("good-report.md"))
    assert s.title is None  # pastes and uploads have no separate title
    assert list(texts(s)) == ["description", "steps_to_reproduce", "expected_behavior",
                              "observed_behavior", "environment"]
    assert texts(s)["steps_to_reproduce"][0].startswith("1. Run `touch config.yaml`")
    refs = [r.text for r in s.code_references]
    assert "src/mytool/config.py:88" in refs and "load_config()" in refs
    assert "v2.4.1" in [v.text for v in s.versions]


def test_missing_steps_sample():
    _, s = structured(sample("missing-steps.md"))
    assert "steps_to_reproduce" not in s.fields
    assert texts(s)["expected_behavior"] == ["The exported PDF contains all pages of the document."]
    assert texts(s)["observed_behavior"][0].startswith("Only the first page")
    assert texts(s)["environment"][0].startswith("1.8.0 on macOS 14")
    assert s.code_references == []


# name: (body, expected {field: [section texts]})   (title is always None unless given)
CASES = {
    "bold note mid-steps stays in steps": (
        "## Steps to reproduce\n1. a\n**Note:** flaky\n2. b\n## Expected\nok",
        {"steps_to_reproduce": ["1. a\n**Note:** flaky\n2. b"], "expected_behavior": ["ok"]}),
    "bold sentence is not a label": (
        "## Steps to reproduce\n1. open\n**Expected** it to open but it closed\n2. close",
        {"steps_to_reproduce": ["1. open\n**Expected** it to open but it closed\n2. close"]}),
    "bold label with colon outside the stars": (
        "**Expected**: x\n**Actual:** y", {"expected_behavior": ["x"], "observed_behavior": ["y"]}),
    "bold label alone on its line": (
        "**Expected**\nx\n**Actual**\ny", {"expected_behavior": ["x"], "observed_behavior": ["y"]}),
    "heading inside fenced code is content": (
        "## Steps\n```\n# Expected\nfoo\n```\n## Expected behavior\nok",
        {"steps_to_reproduce": ["```\n# Expected\nfoo\n```"], "expected_behavior": ["ok"]}),
    "tilde fence": (
        "## Steps\n~~~\n## Expected\n~~~\n## Expected\nok",
        {"steps_to_reproduce": ["~~~\n## Expected\n~~~"], "expected_behavior": ["ok"]}),
    "4-backtick fence is not closed by 3 backticks": (
        "## Steps\n````\n```\n## Expected\n```\n````\n## Actual\nboom",
        {"steps_to_reproduce": ["````\n```\n## Expected\n```\n````"], "observed_behavior": ["boom"]}),
    "heading inside HTML comment is content": (
        "## Steps\n1. a\n<!--\n## Expected behavior\nDescribe here\n-->\n## Actual\nboom",
        {"steps_to_reproduce": ["1. a\n<!--\n## Expected behavior\nDescribe here\n-->"],
         "observed_behavior": ["boom"]}),
    "heading text after a colon is kept": (
        "## Steps\nx\n## Expected: it should save\n## Actual\ncrash",
        {"steps_to_reproduce": ["x"], "expected_behavior": ["it should save"], "observed_behavior": ["crash"]}),
    "empty section is kept": (
        "## Steps\n## Expected\nok", {"steps_to_reproduce": [""], "expected_behavior": ["ok"]}),
    "lone CR is a line break": (
        "## Steps\r1. a\r## Expected\rok", {"steps_to_reproduce": ["1. a"], "expected_behavior": ["ok"]}),
    "CRLF kept exactly": (
        "## Steps to reproduce\r\n1. a\r\n\r\n## Expected\r\nx\r\n",
        {"steps_to_reproduce": ["1. a"], "expected_behavior": ["x"]}),
    "bold labels with inline text": (
        "**Expected:** it works\n**Actual:** nope",
        {"expected_behavior": ["it works"], "observed_behavior": ["nope"]}),
    "unicode and emoji": (
        "## Steps to reproduce ✅\nÜber café\n## \U0001f41b Expected behavior\nnaïve",
        {"steps_to_reproduce": ["Über café"], "expected_behavior": ["naïve"]}),
    "repeated sections are all kept": (
        "## Steps\na\n## Steps\nb", {"steps_to_reproduce": ["a", "b"]}),
    "system startup is not environment": ("# Crash on system startup\nIt crashes.", {}),
    "Conversion fails is not a section": ("# Conversion fails\nIt fails.", {}),
    "C# heading": ("# Crash in C#\nbody", {}),
    "startup, versioning and preversion are unknown": (
        "## Startup\nx\n## Versioning notes\ny\n## Preversion\nz", {}),
    "one-liner": ("it is broken", {}),
    "alias as whole-word prefix": ("## Steps to reproduce the issue\nx", {"steps_to_reproduce": ["x"]}),
    "alias as whole-word suffix": (
        "## Pandas issue description\nboom\n## The installed versions\nv", {"description": ["boom"], "environment": ["v"]}),
    "what happened is observed": (
        "### What happened?\ncrash\n### What did you expect to happen?\nno crash",
        {"observed_behavior": ["crash"], "expected_behavior": ["no crash"]}),
    "what happened instead is observed": ("## What happened instead\nboom", {"observed_behavior": ["boom"]}),
}


@pytest.mark.parametrize("case", CASES)
def test_adversarial_cases(case):
    body, expected = CASES[case]
    raw, s = structured(body)
    assert texts(s) == expected
    assert s.title is None
    assert_nothing_lost(raw, s)


def test_explicit_title_is_kept_and_nothing_is_derived():
    _, s = structured("# Heading\n## Steps\nx", title="Given")
    assert s.title == "Given"
    _, s = structured("# Heading\n## Steps\nx")
    assert s.title is None


def test_unmapped_sections():
    _, s = structured("Hello there\n## Screenshots\nimg\n## Steps\nx")
    assert [(u.label, u.text) for u in s.unmapped] == [(None, "Hello there"), ("Screenshots", "img")]
    _, s = structured("# Conversion fails\nIt fails.")
    assert [(u.label, u.text) for u in s.unmapped] == [("Conversion fails", "It fails.")]


def test_comment_only_section_is_not_meaningful():
    _, s = structured("## Steps\n<!-- describe the steps -->\n## Expected\n<!--\nmulti\nline\n-->\nreal")
    steps, expected = s.fields["steps_to_reproduce"][0], s.fields["expected_behavior"][0]
    assert intake.meaningful_text(steps) == "" and intake.meaningful_text(expected) == "real"
    assert intake.meaningful_text(Section(text="<!-- unclosed", start=0, end=0)) == ""


def test_line_numbers():
    body = "a\r\nb\rc\n\nd"
    assert [intake.line_of(body, i) for i in (0, 3, 5, 7, 8)] == [1, 2, 3, 4, 5]


# Real-world issue-form shapes: which headings must map to which fields.
KUBERNETES = ("### What happened?\n\ncrash\n\n### What did you expect to happen?\n\nno crash\n\n"
              "### How can we reproduce it (as minimally and precisely as possible)?\n\n1. do it\n\n"
              "### Anything else we need to know?\n\nno\n\n### OS version\n\n```console\nLinux\n```\n")
GRAFANA = ("### What happened?\n\ncrash\n\n### What did you expect to happen?\n\nno crash\n\n"
           "### Did this work before?\n\nNo\n\n### How do we reproduce it?\n\n1. do it\n")
PANDAS = ("### Pandas version checks\n\n- [x] checked\n\n### Reproducible Example\n\n```python\nimport pandas\n```\n\n"
          "### Issue Description\n\nboom\n\n### Expected Behavior\n\nfine\n\n### Installed Versions\n\n<details>\nx\n</details>\n")


@pytest.mark.parametrize("body, expected", [
    (KUBERNETES, {"observed_behavior": ["What happened"], "expected_behavior": ["What did you expect to happen?"],
                  "steps_to_reproduce": ["How can we reproduce it (as minimally and precisely as possible)?"],
                  "environment": ["OS version"]}),
    (GRAFANA, {"observed_behavior": ["What happened"], "expected_behavior": ["What did you expect to happen?"],
               "steps_to_reproduce": ["How do we reproduce it?"]}),
    (PANDAS, {"steps_to_reproduce": ["Reproducible Example"], "description": ["Issue Description"],
              "expected_behavior": ["Expected Behavior"], "environment": ["Installed Versions"]}),
])
def test_issue_form_fixtures(body, expected):
    raw, s = structured(body)
    got = {f: [x.label for x in secs] for f, secs in s.fields.items()}
    # compare ignoring the trailing "?" the heading regex keeps
    assert {f: [l.rstrip("?") for l in ls] for f, ls in got.items()} == \
           {f: [l.rstrip("?") for l in ls] for f, ls in expected.items()}
    assert_nothing_lost(raw, s)


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

"""INT-2 Verification: compare the original with the structured version; nothing lost or added.
Sections follow the IE draft v1 (Section object); spans stay exact."""
import pytest

from bugs26.integration import intake, pipeline
from bugs26.integration.models import IELines
from bugs26.stubs.input_evaluation_stub import meaningful_text
from conftest import NAMES, sample


def structured(body, title=""):
    raw = intake.receive(body, "paste", title=title)
    s = intake.structure(raw)
    intake.verify_structured(raw, s)
    return raw, s


def texts(s):
    """Values of the recognized sections by semantic concept."""
    out = {}
    for x in s.sections:
        if x.semantic_concept:
            out.setdefault(x.semantic_concept, []).append(x.value)
    return out


def assert_nothing_lost(raw, s):
    """Cut every section value and the preamble (before the first heading; it stays in raw_body only) out of the
    body: what is left may only be marker lines (heading or bold label) whose label is the label of a section."""
    body = raw.raw_body
    if not s.sections:
        return  # free-form: sections [] and the whole text is in raw_body
    labels = {x.original_label for x in s.sections}
    rest = body
    for x in sorted(s.sections, key=lambda x: -s.spans[x.section_id][0]):
        a, b = s.spans[x.section_id]
        rest = rest[:a] + rest[b:]
    first = s.sections[0].source_lines.start
    rest = rest[len("\n".join(body.split("\n")[:first - 1])) + (1 if first > 1 else 0):]
    for line in rest.splitlines():
        label = line.strip().lstrip("#").strip().strip("*: \t").strip()
        assert not label or label in labels, f"lost text: {line!r}"


@pytest.mark.parametrize("name", NAMES)
def test_span_invariant_on_samples(name):
    raw, s = structured(sample(name))
    for sec in s.sections:
        a, b = s.spans[sec.section_id]
        assert raw.raw_body[a:b] == sec.value
    assert raw.raw_body == sample(name)
    assert_nothing_lost(raw, s)


def test_good_report():
    _, s = structured(sample("good-report.md"))
    assert list(texts(s)) == ["bug_description", "steps_to_reproduce", "expected_behavior",
                              "observed_behavior", "environment_version"]
    assert texts(s)["steps_to_reproduce"][0].startswith("1. Run `touch config.yaml`")
    assert s.extraction.mode == "structured" and s.extraction.template_id is None
    assert all(x.field_id is None and x.required is None for x in s.sections)  # template not known


def test_missing_steps_sample():
    _, s = structured(sample("missing-steps.md"))
    assert "steps_to_reproduce" not in texts(s)  # no section is invented for a missing heading ("absent" needs a template)
    assert texts(s)["expected_behavior"] == ["The exported PDF contains all pages of the document."]
    assert texts(s)["observed_behavior"][0].startswith("Only the first page")
    assert texts(s)["environment_version"][0].startswith("1.8.0 on macOS 14")


# name: (body, expected {concept: [section values]})
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
    "freeform text without markers has no sections": ("it is broken", {}),
    "freeform with a fence and a note": ("Crash.\n**Note:** x\n```\n# Expected\n```", {}),
    "OBS-style version heading": ("## OBS Studio Version\n32.0.1\n## Operating System Info\nWin", {"environment_version": ["32.0.1", "Win"]}),
    "Ollama and Kubernetes version headings": ("### Ollama version\n0.5\n### Kubernetes version\n1.30", {"environment_version": ["0.5", "1.30"]}),
    "ansible-style headings": ("### Summary\ns\n### Issue Type\nBug\n### OS / Environment\nLinux\n### Steps to Reproduce\nx\n### Expected Results\ny\n### Actual Results\nz",
                               {"bug_description": ["s"], "environment_version": ["Linux"], "steps_to_reproduce": ["x"], "expected_behavior": ["y"], "observed_behavior": ["z"]}),
    "current behavior and what is the issue": ("## What is the issue?\na\n## Current Behavior\nb", {"bug_description": ["a"], "observed_behavior": ["b"]}),
    "single-word suffix only for version": ("## Release summary\nx\n## Python version\n3.12\n## Bug platform\ny", {"environment_version": ["3.12"]}),
    "alias as whole-word prefix": ("## Steps to reproduce the issue\nx", {"steps_to_reproduce": ["x"]}),
    "alias as whole-word suffix": (
        "## Pandas issue description\nboom\n## The installed versions\nv", {"bug_description": ["boom"], "environment_version": ["v"]}),
    "what happened is observed": (
        "### What happened?\ncrash\n### What did you expect to happen?\nno crash",
        {"observed_behavior": ["crash"], "expected_behavior": ["no crash"]}),
    "what happened instead is observed": ("## What happened instead\nboom", {"observed_behavior": ["boom"]}),
    "supporting evidence concept": ("## Logs\nTraceback x\n## Screenshots\nimg", {"supporting_evidence": ["Traceback x", "img"]}),
}


@pytest.mark.parametrize("case", CASES)
def test_adversarial_cases(case):
    body, expected = CASES[case]
    raw, s = structured(body)
    assert texts(s) == expected
    assert_nothing_lost(raw, s)


def test_ie_draft_example_a1():
    """Appendix A.1 of the IE draft: same sections, statuses, concepts and lines (also the last, blank section: 11-12)."""
    body = ("### What happened?\nThe Save dialog shows Error E42 after clicking Save.\n### Steps to reproduce\n"
            "Open a new document, type hello, then click Save.\n### Expected behavior\nThe document should be saved.\n"
            "### Version\n2.3.1 on Windows 11.\n### Evidence\nError E42: write failed.\n### Additional details\n")
    _, s = structured(body)
    got = [(x.section_id, x.original_label, x.status, x.value, x.recognition, x.semantic_concept,
            (x.source_lines.start, x.source_lines.end)) for x in s.sections]
    assert got == [
        ("s1", "What happened?", "provided", "The Save dialog shows Error E42 after clicking Save.", "recognized", "observed_behavior", (1, 2)),
        ("s2", "Steps to reproduce", "provided", "Open a new document, type hello, then click Save.", "recognized", "steps_to_reproduce", (3, 4)),
        ("s3", "Expected behavior", "provided", "The document should be saved.", "recognized", "expected_behavior", (5, 6)),
        ("s4", "Version", "provided", "2.3.1 on Windows 11.", "recognized", "environment_version", (7, 8)),
        ("s5", "Evidence", "provided", "Error E42: write failed.", "recognized", "supporting_evidence", (9, 10)),
        ("s6", "Additional details", "blank", "", "unrecognized", None, (11, 12)),
    ]


def test_freeform_has_no_sections_and_no_invented_description():
    raw, s = structured("  it is broken  \n")
    assert s.sections == [] and s.extraction.mode == "free_form" and s.spans == {}
    assert raw.raw_body == "  it is broken  \n"


def test_preamble_is_not_a_section_and_unknown_headings_are_diagnosed():
    raw, s = structured("Hello there\n## Foo\nimg\n## Steps\nx")
    assert [(x.original_label, x.value, x.recognition, x.semantic_concept) for x in s.sections] == [
        ("Foo", "img", "unrecognized", None), ("Steps", "x", "recognized", "steps_to_reproduce")]
    assert "Hello there" in raw.raw_body and not any("Hello there" in (x.value or "") for x in s.sections)
    assert s.extraction.mode == "structured" and s.extraction.diagnostics == []  # `recognition` says what was not matched
    _, s = structured("# Conversion fails\nIt fails.")
    assert [(x.original_label, x.value) for x in s.sections] == [("Conversion fails", "It fails.")]


def test_status_blank_provided_and_exact_values():
    _, s = structured("## Steps\n\n  \n## Expected\n_No response_\n## Actual\n<!-- fill in -->")
    steps, expected, actual = s.sections
    assert (steps.status, steps.value) == ("blank", "\n  \n")  # exact whitespace string
    assert (expected.status, expected.value) == ("provided", "_No response_")  # copied exactly; IE decides
    assert (actual.status, actual.value) == ("provided", "<!-- fill in -->")
    assert all(x.status != "absent" for x in s.sections)


def test_lines_split_on_lf_and_crlf_is_one_break():
    _, s = structured("intro\r\n## Steps\r\nx\r\ny\r\n## Expected\r\nz")
    assert [(x.source_lines.start, x.source_lines.end) for x in s.sections] == [(2, 4), (5, 6)]


def test_title_is_never_derived_from_the_body():
    assert structured("# Heading\n## Steps\nx")[0].title == ""
    assert structured("x", title="Given")[0].title == "Given"


def test_comment_only_section_is_not_meaningful_to_the_stub():
    _, s = structured("## Steps\n<!-- describe the steps -->\n## Expected\n<!--\nmulti\nline\n-->\nreal")
    steps, expected = s.sections
    assert meaningful_text(steps) == "" and meaningful_text(expected) == "real"


# Real-world issue-form shapes: which headings must map to which concepts.
KUBERNETES = ("### Kubernetes version\n\n1.30\n\n### What happened?\n\ncrash\n\n### What did you expect to happen?\n\nno crash\n\n"
              "### How can we reproduce it (as minimally and precisely as possible)?\n\n1. do it\n\n"
              "### Anything else we need to know?\n\nno\n\n### OS version\n\n```console\nLinux\n```\n")
GRAFANA = ("### What happened?\n\ncrash\n\n### What did you expect to happen?\n\nno crash\n\n"
           "### Did this work before?\n\nNo\n\n### How do we reproduce it?\n\n1. do it\n")
PANDAS = ("### Pandas version checks\n\n- [x] checked\n\n### Reproducible Example\n\n```python\nimport pandas\n```\n\n"
          "### Issue Description\n\nboom\n\n### Expected Behavior\n\nfine\n\n### Installed Versions\n\n<details>\nx\n</details>\n")


@pytest.mark.parametrize("body, expected", [
    (KUBERNETES, {"observed_behavior": ["What happened?"], "expected_behavior": ["What did you expect to happen?"],
                  "steps_to_reproduce": ["How can we reproduce it (as minimally and precisely as possible)?"],
                  "environment_version": ["Kubernetes version", "OS version"]}),
    (GRAFANA, {"observed_behavior": ["What happened?"], "expected_behavior": ["What did you expect to happen?"],
               "steps_to_reproduce": ["How do we reproduce it?"]}),
    (PANDAS, {"steps_to_reproduce": ["Reproducible Example"], "bug_description": ["Issue Description"],
              "expected_behavior": ["Expected Behavior"], "environment_version": ["Installed Versions"]}),
])
def test_issue_form_fixtures(body, expected):
    raw, s = structured(body)
    got = {}
    for x in s.sections:
        if x.semantic_concept:
            got.setdefault(x.semantic_concept, []).append(x.original_label)
    assert got == expected
    assert_nothing_lost(raw, s)


def test_verify_catches_a_wrong_span():
    raw, s = structured("## Steps\nabc")
    s.sections[0].value = "abd"
    with pytest.raises(intake.PreparationError):
        intake.verify_structured(raw, s)


def test_verify_catches_wrong_lines_label_and_status():
    for change in (lambda x: setattr(x, "source_lines", IELines(start=1, end=1)),   # value is on line 2
                   lambda x: setattr(x, "source_lines", IELines(start=2, end=2)),   # label is on line 1
                   lambda x: setattr(x, "original_label", "Other"),
                   lambda x: setattr(x, "status", "blank")):
        raw, s = structured("## Steps\nabc")
        change(s.sections[0])
        with pytest.raises(intake.PreparationError):
            intake.verify_structured(raw, s)


def test_no_response_is_provided_text_only_the_stub_ignores_it():
    _, s = structured("### Steps\n_No response_\n### Expected\n<!-- fill in -->\n### Actual\nboom")
    assert [x.value for x in s.sections] == ["_No response_", "<!-- fill in -->", "boom"]
    assert [meaningful_text(x) for x in s.sections] == ["", "", "boom"]


def test_all_headings_unrecognized_is_an_unsupported_template():
    out = pipeline.run("## Etapes\nun\n## Resultat\ndeux", "paste")
    ext = out.record.extraction
    assert ext.mode == "unsupported_template" and [d.code for d in ext.diagnostics] == ["no_headings_recognised"]
    assert [s.recognition for s in out.record.sections] == ["unrecognized", "unrecognized"]  # still sent: they are valid input
    assert not any("Etapes" in c or "recognised" in c for c in out.could_not_check)  # D6: IE reads the raw text

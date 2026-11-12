"""Integration's side of the IE interface agreement, Section 7 (Verification).
Draft: Input-evaluation branch, documentation/Interface Agreemtn/input-evaluation-integration.md.
One test (or small group) per Section 7 row that Integration performs or checks. Test names: test_IF_<n>_...
Mocks: the GitHub API (github._http_get) and Input Evaluation (fake evaluators); nothing touches the network."""
import copy
import json
import logging
import re
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from integration import github, intake, pipeline, route
from integration.intake import InputEvaluationError
from integration.models import (CRITERIA, CIRequest, IEClaim, IEClaimExtraction, IEDiagnostic, IEEvidence,
                                       IELines, IEResult)
from integration.web import app
from conftest import NAMES, ci_result, ie_result, sample

EX = json.loads((Path(__file__).parent / "ie_examples.json").read_text(encoding="utf-8"))
ISSUE_URL = "https://github.com/o/r/issues/7"  # conftest makes o/r the supported repo
CONCEPTS = {"bug_description", "steps_to_reproduce", "expected_behavior", "observed_behavior", "environment_version",
            "supporting_evidence"}
PENDING = "pending transport decision (IE open item 3, 2026-11-24)"


# --- helpers ----------------------------------------------------------------------------------

def gh_payload(number=7, title="Crash on ‘Save’ — naïve 日本語 \U0001F41B",
               body="### What happened?\r\nSave crashes with éè and \U0001F600.\r\n\r\n### Steps to reproduce\r\n"
                    "1. Open\r\n2. Save \r\n  indented line\twith tab\r\n",
               login="octocat-secret"):
    """A realistic GitHub REST issue payload, with person fields that must never reach us (INT-9)."""
    return {
        "url": f"https://api.github.com/repos/o/r/issues/{number}", "id": 1234567890 + number, "node_id": "I_kwDOA",
        "number": number, "title": title, "body": body, "state": "open", "locked": False, "comments": 3,
        "html_url": f"https://github.com/o/r/issues/{number}",
        "user": {"login": login, "id": 583231, "avatar_url": f"https://avatars.githubusercontent.com/u/583231?v=4",
                 "html_url": f"https://github.com/{login}", "type": "User", "site_admin": False},
        "assignee": {"login": "maintainer-x", "id": 9}, "assignees": [{"login": "maintainer-x", "id": 9}],
        "labels": [{"id": 1, "name": "bug", "color": "d73a4a", "description": "Something isn't working"},
                   {"id": 2, "name": "good first issue ✨", "color": "7057ff"}],
        "author_association": "CONTRIBUTOR",
        "created_at": "2026-11-01T14:00:00Z", "updated_at": "2026-11-02T09:30:15Z", "closed_at": None,
    }


def mock_github(monkeypatch, *payloads):
    by_number = {p["number"]: p for p in payloads}
    monkeypatch.setattr(github, "_http_get", lambda url: copy.deepcopy(by_number[int(url.rsplit("/", 1)[1])]))


class Recorder:
    """Fake IE: records the record it was given, answers with `make(record)`."""
    def __init__(self, make=None):
        self.make, self.records = make, []

    def evaluate(self, record):
        self.records.append(record)
        return self.make(record) if self.make else ie_result(record)


class RecordingCI:
    def __init__(self):
        self.requests = []

    def investigate(self, request):
        self.requests.append(request)
        return ci_result(request)


def run_github(url=ISSUE_URL, evaluator=None, investigator=None):
    found = github.fetch_issue(url)
    meta = {k: found[k] for k in ("issue_number", "labels", "created_at", "updated_at")}
    return pipeline.run(found["body"], "github", found["repo_url"], title=found["title"], issue_url=found["issue_url"],
                        evaluator=evaluator, investigator=investigator, **meta)


def lines_text(body, lines):
    return "\n".join(body.split("\n")[lines.start - 1:lines.end])  # LF split; a CRLF is one break


def all_keys(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield k
            yield from all_keys(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from all_keys(v)


def result_for(record, name, **changes):
    """Draft example `name` (A.4/A.5/A.6) answering `record`: only the correlation ids are replaced."""
    d = copy.deepcopy(EX[name])
    d.update(request_id=record.request_id, snapshot_id=record.snapshot_id, **changes)
    return IEResult.model_validate(d)


def a5_partial(record):
    d = copy.deepcopy(EX["A.5"])
    d["criterion_findings"][5] = EX["A.7"]  # C6 unevaluated, as in the draft's note under A.7
    d.update(processing_status="partial", unevaluated_criteria=["C6"], request_id=record.request_id,
             snapshot_id=record.snapshot_id,
             diagnostics=[{"severity": "error", "code": "dependency_unavailable", "path": None,
                           "message": "Evidence-access service unavailable; screenshot not checked."}])
    return IEResult.model_validate(d)


# --- IF-1, IF-2 -------------------------------------------------------------------------------

def test_IF_1_IF_2_github_issue_is_passed_on_character_for_character(monkeypatch):
    """Section 7: "Run Integration on real issues and on A.1 and A.2. Compare title, body, and metadata with the
    GitHub source character by character." (Real issues are replaced by a realistic mocked GitHub API payload:
    CRLF, unicode, emoji, nbsp, tabs, labels as objects, timestamps, and a `user` object.)"""
    payload = gh_payload()
    mock_github(monkeypatch, payload)
    ie = Recorder()
    out = run_github(evaluator=ie)
    (rec,) = ie.records
    assert rec.title == payload["title"] and rec.raw_body == payload["body"]  # == is character by character
    assert "\r\n" in rec.raw_body and rec.raw_body.encode("utf-8") == payload["body"].encode("utf-8")
    assert (rec.repository, rec.issue_number, rec.issue_url) == ("o/r", 7, payload["html_url"])
    assert rec.labels == ["bug", "good first issue ✨"]
    assert (rec.created_at, rec.updated_at) == (payload["created_at"], payload["updated_at"])
    assert rec.body_source == "current"  # the initial text is not available; the draft requires this to be honest
    assert out.record == rec  # the output carries the same snapshot
    dumped = json.loads(out.model_dump_json())
    assert "user" not in set(all_keys(dumped)) and "octocat-secret" not in json.dumps(dumped)
    assert "user" not in IEResult.model_fields and "user" not in type(rec).model_fields


def test_IF_1_IF_2_a_null_body_is_sent_as_empty_string(monkeypatch):
    """Section 7: "Compare title, body, and metadata with the GitHub source character by character."
    (Draft 4.1: a body GitHub returns as null is sent as "".)"""
    mock_github(monkeypatch, {**gh_payload(), "body": None, "labels": []})
    ie = Recorder()
    run_github(evaluator=ie)
    assert ie.records[0].raw_body == "" and ie.records[0].labels == [] and ie.records[0].sections == []


@pytest.mark.parametrize("name", ["A.1", "A.2"])
def test_IF_1_IF_2_draft_records_a1_a2(name):
    """Section 7: "Run Integration on real issues and on A.1 and A.2. Compare title, body, and metadata with the
    GitHub source character by character." (Integration's record equals the draft's except the ids, which are
    ours, and body_source, which is "current".)"""
    ex = EX[name]
    ie = Recorder()
    pipeline.run(ex["raw_body"], "github", "https://github.com/example/editor", title=ex["title"],
                 issue_url=ex["issue_url"], issue_number=ex["issue_number"], labels=ex["labels"],
                 created_at=ex["created_at"], updated_at=ex["updated_at"], evaluator=ie)
    sent = json.loads(ie.records[0].model_dump_json())
    assert set(sent) == set(ex)  # all fields, none added (no user/author)
    skip = {"request_id", "snapshot_id", "body_source"}
    assert {k: v for k, v in sent.items() if k not in skip} == {k: v for k, v in ex.items() if k not in skip}
    assert sent["request_id"] and sent["snapshot_id"] and sent["request_id"] != sent["snapshot_id"]


# --- IF-3 -------------------------------------------------------------------------------------

BODY_LF = (
    "### What happened?\nThe Save dialog shows Error E42 — naïve 日本語.\n"
    "### Steps to reproduce\n1. Open\n2. Save\n"
    "### Expected behavior\n_No response_\n"
    "### Additional details\n"
    "### Notes\n   \n"
    "### Steps to reproduce\nSecond attempt: same steps.\n"
    "### My own heading\nFree text.\n"
    "### Version\n2.3.1\n")


def structured(body):
    raw = intake.receive(body, "paste", title="T")
    s = intake.structure(raw)
    intake.verify_structured(raw, s)  # Integration's own preparation check also passes
    return raw, s, intake.to_record(raw, s)


@pytest.mark.parametrize("body", [BODY_LF, BODY_LF.replace("\n", "\r\n")], ids=["LF", "CRLF"])
def test_IF_3_provided_blank_unrecognized_repeated_sections(body):
    """Section 7: "Fixtures with provided, blank, absent, unrecognized, and repeated sections. Check the encodings
    and that every `value` is found in its `source_lines`." (absent: see test_IF_3_absent_is_never_emitted.)"""
    raw, s, record = structured(body)
    sections = record.sections
    by_label = [(x.original_label, x.status, x.recognition, x.semantic_concept) for x in sections]
    assert by_label == [
        ("What happened?", "provided", "recognized", "observed_behavior"),
        ("Steps to reproduce", "provided", "recognized", "steps_to_reproduce"),
        ("Expected behavior", "provided", "recognized", "expected_behavior"),  # "_No response_" is still provided
        ("Additional details", "blank", "unrecognized", None),
        ("Notes", "blank", "unrecognized", None),                              # whitespace only
        ("Steps to reproduce", "provided", "recognized", "steps_to_reproduce"),  # repeated: a separate section
        ("My own heading", "provided", "unrecognized", None),                  # unknown heading kept, still valid
        ("Version", "provided", "recognized", "environment_version")]
    assert len({x.section_id for x in sections}) == len(sections) and all(x.section_id for x in sections)
    assert sections[2].value == "_No response_"
    assert sections[3].value == "" and sections[4].value == "   " and sections[4].value in raw.raw_body
    assert sections[1].value != sections[5].value  # not merged
    nl = "\r\n" if "\r\n" in body else "\n"
    assert sections[1].value == f"1. Open{nl}2. Save"  # exact text, inner line break kept
    for x in sections:
        assert x.field_id is None and x.required is None  # template unknown
        assert x.semantic_concept is None or (x.semantic_concept in CONCEPTS and x.recognition == "recognized")
        assert x.source_lines is not None
        # strict: every value, blank ones included (they leave out their final line break), is inside its source_lines
        assert x.value in lines_text(raw.raw_body, x.source_lines)
        assert x.value in raw.raw_body
        assert x.original_label in lines_text(raw.raw_body, IELines(start=x.source_lines.start, end=x.source_lines.start))
    # encodings: the record round-trips as JSON with these exact strings
    back = json.loads(record.model_dump_json())
    assert back["sections"][0]["value"] == sections[0].value and back["raw_body"] == body
    assert back["extraction"] == {"mode": "structured", "template_id": None, "diagnostics": []}


def test_IF_3_all_unrecognized_headings_are_valid_structured_input():
    """Section 7: "Fixtures with provided, blank, absent, unrecognized, and repeated sections. Check the encodings
    and that every `value` is found in its `source_lines`." (Draft 4.1: diagnostics non-empty for
    unsupported_template.)"""
    raw, s, record = structured("### Foo\nbar\n### Baz\nqux\n")
    assert record.extraction.mode == "structured" and record.extraction.diagnostics == []  # unsupported_template: not emitted yet
    assert {x.recognition for x in record.sections} == {"unrecognized"} and record.raw_body == raw.raw_body


def test_IF_3_free_form_has_no_sections():
    """Section 7: "Fixtures with provided, blank, absent, unrecognized, and repeated sections. Check the encodings
    and that every `value` is found in its `source_lines`." (Free-form: `sections: []`, never invented.)"""
    _, _, record = structured("It does not work. Please help.")
    assert record.sections == [] and record.extraction.mode == "free_form"


@pytest.mark.parametrize("body", [BODY_LF, BODY_LF.replace("\n", "\r\n"), "plain text", "### Only\n", ""])
def test_IF_3_absent_is_never_emitted(body):
    """Section 7: "Fixtures with provided, blank, absent, unrecognized, and repeated sections." Integration may emit
    `absent` only for a field of a KNOWN template (extraction.template_id not null; draft 4.1). Integration has no
    issue-template support yet (open item 2: field_id/required/template_id), so template_id is always null and
    `absent` must never be emitted, nor invented for headings it cannot identify."""
    _, s, record = structured(body)
    assert record.extraction.template_id is None
    assert "absent" not in {x.status for x in record.sections}
    assert all(x.value is not None and x.source_lines is not None for x in record.sections)  # absent would be null/null


# --- IF-5 (Integration checks it is shown as a failure) ---------------------------------------

def with_ie(monkeypatch, evaluator):
    real = pipeline.run
    monkeypatch.setattr("integration.web.pipeline.run", lambda *a, **k: real(*a, evaluator=evaluator, **k))


def a4_for(record):
    return result_for(record, "A.4")


def failed_for(record):
    return IEResult.model_validate({**EX["A.4"], "request_id": record.request_id, "snapshot_id": record.snapshot_id,
                                    "processing_status": "failed",
                                    "diagnostics": [{"severity": "error", "code": "internal_error", "path": None,
                                                     "message": "Criteria could not be loaded."}]})


@pytest.mark.parametrize("make, banner", [(a4_for, "Input Evaluation rejected this report"),
                                          (failed_for, "Input Evaluation failed"),
                                          (lambda r: IEResult.model_validate(  # A.4 with null ids: matched by the call
                                              {**EX["A.4"], "request_id": None, "snapshot_id": None}),
                                           "Input Evaluation rejected this report")],
                         ids=["A.4", "failed", "A.4-null-ids"])
def test_IF_5_invalid_input_result_is_shown_as_a_failure(monkeypatch, make, banner):
    """Section 7: "Expect `invalid_input` with the right path and no findings (A.3, A.4)." Performed by IE;
    "Integration checks it is shown as a failure": a valid invalid_input/failed result reaches the maintainer as a
    red failure banner, no findings, no claims, no Claim Investigation call, and a could_not_check entry."""
    ci = RecordingCI()
    out = pipeline.run("It does not work. Please help.", "paste", title="Something is wrong",
                       evaluator=Recorder(make), investigator=ci)
    assert out.ie.processing_status in ("invalid_input", "failed") and out.ie.criterion_findings == []
    assert out.ie.identified_claims == [] and ci.requests == [] and out.ci_results == []
    assert any("Input Evaluation returned" in x for x in out.could_not_check)
    assert any(d.severity == "error" for d in out.ie.diagnostics)
    with_ie(monkeypatch, Recorder(make))
    page = TestClient(app).post("/evaluate", data={"text": "It does not work. Please help."}).text
    assert banner in page and "Evaluation completed" not in page
    assert not any(f"C{i} {CRITERIA[f'C{i}']}" in page for i in range(1, 8))  # no finding rendered
    assert "No criterion was evaluated; claims were not extracted" in page and "No claims were identified" not in page
    assert any("No criterion was evaluated: Input Evaluation returned" in x for x in out.could_not_check)


def bad_results():
    """Contract-violating results (draft 4.2/4.3), each built from a valid one by one change."""
    def mk(edit):
        def make(record):
            d = json.loads(a5_partial(record).model_dump_json())
            d["criterion_findings"][5] = copy.deepcopy(EX["A.5"]["criterion_findings"][5])
            d.update(processing_status="completed", unevaluated_criteria=[], diagnostics=[])
            d["claim_extraction"] = {"status": "completed", "reason": None}
            edit(d)
            return IEResult.model_validate(d)
        return make
    return {
        "invalid_input_with_findings": mk(lambda d: d.update(processing_status="invalid_input")),
        "completed_with_six_findings": mk(lambda d: d["criterion_findings"].pop()),
        "duplicate_criterion": mk(lambda d: d["criterion_findings"][6].update(criterion_id="C1")),
        "completed_with_error_diagnostic": mk(lambda d: d.update(diagnostics=[
            {"severity": "error", "code": "internal_error", "path": None, "message": "x"}])),
        "wrong_request_id": mk(lambda d: d.update(request_id="req-other")),
        "wrong_snapshot_id": mk(lambda d: d.update(snapshot_id="snap-other")),
        "unevaluated_list_mismatch": mk(lambda d: d.update(unevaluated_criteria=["C2"])),
        "criteria_version_differs": mk(lambda d: d["criterion_findings"][0].update(criteria_version="other")),
        "repeated_claim_id": mk(lambda d: d.update(identified_claims=d["identified_claims"] * 2)),
        "no_checkable_claims_wrong": mk(lambda d: d.update(no_checkable_claims=True)),
        "quote_not_in_body": mk(lambda d: d["criterion_findings"][0]["evidence"][0].update(quote="never written")),
    }


@pytest.mark.parametrize("name", list(bad_results()))
def test_IF_5_contract_violating_result_is_a_failure_and_no_findings_are_rendered(monkeypatch, name):
    """Section 7: "Expect `invalid_input` ... and no findings (A.3, A.4)." Performed by IE; "Integration checks it
    is shown as a failure": a result that breaks the draft is never shown as an evaluation. pipeline.run raises
    InputEvaluationError and the web page is the 502 error page with no findings."""
    make = bad_results()[name]
    body, title = EX["A.1"]["raw_body"], EX["A.1"]["title"]
    ci = RecordingCI()
    with pytest.raises(InputEvaluationError, match="invalid result"):
        pipeline.run(body, "paste", title=title, evaluator=Recorder(make), investigator=ci)
    assert ci.requests == []
    with_ie(monkeypatch, Recorder(make))
    r = TestClient(app).post("/evaluate", data={"text": body})
    assert r.status_code == 502 and "Input Evaluation" in r.text
    assert "Evaluation completed" not in r.text and "C1 Bug description" not in r.text and "Download JSON" not in r.text


@pytest.mark.parametrize("returned", [None, {"schema_version": "1.0"}, "nonsense"], ids=["None", "dict-missing", "str"])
def test_IF_5_unusable_result_is_a_failure(returned):
    """Section 7: "Integration checks it is shown as a failure": a missing or malformed result object is a failure."""
    class Ev:
        def evaluate(self, record):
            return returned
    with pytest.raises(InputEvaluationError):
        pipeline.run("x", "paste", evaluator=Ev())


# --- IF-6 (Integration inspects) --------------------------------------------------------------

def quotation_problems(raw, ie):
    """Independent re-check (does not call route.match_ie): C1-C7 exactly once, every quotation in its source."""
    problems = []
    if ie.processing_status in ("completed", "partial") and sorted(f.criterion_id for f in ie.criterion_findings) != sorted(CRITERIA):
        problems.append("criteria")
    evid = [e for f in ie.criterion_findings for e in f.evidence] + [c.source for c in ie.identified_claims]
    for e in evid:
        if e.basis != "quotation":
            continue
        src = {"title": raw.title, "raw_body": raw.raw_body, "whole_report": raw.title + "\n" + raw.raw_body}[e.source]
        if e.lines is not None:
            src = lines_text(src, e.lines)
        if not e.quote or e.quote not in src:
            problems.append(f"quote {e.quote!r}")
    return problems


@pytest.mark.parametrize("name", NAMES)
def test_IF_6_every_result_has_c1_to_c7_once_and_quotations_are_in_the_source(name):
    """Section 7: "Check that every result has C1-C7 once and every quotation is found in the source. Both owners
    inspect a sample of findings to confirm the evidence supports them." Integration side: run the placeholder IE
    on each sample report and check both properties independently of match_ie. (The human sample inspection is
    not automatable and is not claimed here.)"""
    text = sample(name)
    out = pipeline.run(text, "paste", title="T")
    raw = intake.receive(text, "paste", title="T")
    assert [f.criterion_id for f in out.ie.criterion_findings] == list(CRITERIA)
    assert quotation_problems(raw, out.ie) == []


@pytest.mark.parametrize("name, req", [("A.5", "A.1"), ("A.6", "A.2")])
def test_IF_6_draft_results_a5_a6_pass(name, req):
    """Section 7: "Check that every result has C1-C7 once and every quotation is found in the source."
    (A.5 and A.6 against the A.1 and A.2 text; A.6 also quotes the title.)"""
    raw = intake.receive(EX[req]["raw_body"], "paste", title=EX[req]["title"])
    raw = raw.model_copy(update=dict(request_id=EX[name]["request_id"], snapshot_id=EX[name]["snapshot_id"]))
    ie = IEResult.model_validate(EX[name])
    route.match_ie(raw, ie)
    assert quotation_problems(raw, ie) == []


def test_IF_6_crlf_line_numbers_count_a_crlf_as_one_break():
    """Section 7: "... every quotation is found in the source." (Draft 4.2: lines are numbered by splitting
    raw_body on line feeds; \\r\\n counts as one break.)"""
    body = "intro\r\nSave fails\r\nwith E42\r\n"
    rec = intake.receive(body, "paste", title="T")

    def result(start, end, quote):
        ev = IEEvidence(basis="quotation", source="raw_body", section_id=None, lines=IELines(start=start, end=end),
                        quote=quote, explanation="e")
        r = ie_result(rec)
        r.criterion_findings[0].evidence[:] = [ev]
        return r
    route.match_ie(rec, result(2, 2, "Save fails"))
    route.match_ie(rec, result(2, 3, "Save fails\r\nwith E42"))
    for bad in (result(1, 1, "Save fails"), result(3, 3, "Save fails"), result(2, 2, "Save fails with E42")):
        with pytest.raises(InputEvaluationError, match="quotation"):
            route.match_ie(rec, bad)


@pytest.mark.parametrize("source, quote, ok", [("title", "Something is wrong", True), ("title", "Other", False),
                                               ("raw_body", "Please help", True), ("raw_body", "Something is wrong", False),
                                               ("whole_report", "Something is wrong", True), ("whole_report", "nope", False)])
def test_IF_6_quotation_source_is_checked(source, quote, ok):
    """Section 7: "Check that ... every quotation is found in the source." (title / raw_body / whole_report.)"""
    rec = intake.receive("It does not work. Please help.", "paste", title="Something is wrong")
    r = ie_result(rec)
    r.criterion_findings[0].evidence[:] = [IEEvidence(basis="quotation", source=source, section_id=None, lines=None,
                                                      quote=quote, explanation="e")]
    if ok:
        route.match_ie(rec, r)
    else:
        with pytest.raises(InputEvaluationError, match="quotation"):
            route.match_ie(rec, r)


def test_IF_6_claim_source_quotation_must_be_in_the_body():
    """Section 7: "... every quotation is found in the source." (The claim `source` is a quotation too, draft 4.2.)"""
    rec = intake.receive("The Save dialog shows Error E42.", "paste")
    bad = IEClaim(claim_id="c1", claim_text="Error E99", relevant_context="Error E99",
                  source=IEEvidence(basis="quotation", source="raw_body", section_id=None, lines=IELines(start=1, end=1),
                                    quote="Error E99", explanation="e"), named_project_versions=[])
    with pytest.raises(InputEvaluationError, match="claim c1 source"):
        route.match_ie(rec, ie_result(rec, claims=[bad]))


# --- IF-8 (Integration checks forwarding) -----------------------------------------------------

BODY8 = ("### What happened?\nSave fails with Error E42 in 2.3.1.\nIt worked in 2.2.0 but fails since 2.3.1.\n"
         "### Steps\nOpen `main.py` and call `save()`.\n")


def claim_in(body, text, cid, versions=(), context=None):
    ln = body[:body.index(text)].count("\n") + 1
    return IEClaim(claim_id=cid, claim_text=text, relevant_context=context or text,
                   source=IEEvidence(basis="quotation", source="raw_body", section_id=None,
                                     lines=IELines(start=ln, end=ln), quote=text, explanation=f"why {cid}"),
                   named_project_versions=list(versions))


def run8(claims, **changes):
    ie, ci = Recorder(lambda r: ie_result(r, claims=claims, **changes)), RecordingCI()
    before = copy.deepcopy([c.model_dump() for c in claims])
    out = pipeline.run(BODY8, "github", "https://github.com/o/r", title="T", issue_url=ISSUE_URL, issue_number=7,
                       evaluator=ie, investigator=ci)
    assert [c.model_dump() for c in claims] == before  # the claims were not modified in place
    return out, ci, ie.records[0]


def assert_forwarded(ci, record, claims):
    assert len(ci.requests) == len(claims)
    for req, claim in zip(ci.requests, claims):  # same order, one request per claim, nothing changed
        assert isinstance(req, CIRequest)
        assert (req.request_id, req.snapshot_id) == (record.request_id, record.snapshot_id)
        assert req.claim_id == claim.claim_id and req.claim_text == claim.claim_text
        assert req.source == claim.source and req.relevant_context == claim.relevant_context
        assert req.named_project_versions == claim.named_project_versions
        assert (req.title, req.raw_body, req.issue_url, req.repository) == ("T", BODY8, ISSUE_URL, "o/r")


def test_IF_8_several_claims_each_forwarded_untouched():
    """Section 7: "Reports with several claims, one named version, two compared versions, no claims (A.6), and
    interrupted extraction." IE; "Integration checks forwarding": three claims give exactly three CI requests."""
    claims = [claim_in(BODY8, "Save fails with Error E42 in 2.3.1.", "claim-1", ["2.3.1"]),
              claim_in(BODY8, "Open `main.py` and call `save()`.", "claim-2", [],
                       context="### Steps\nOpen `main.py` and call `save()`."),
              claim_in(BODY8, "It worked in 2.2.0 but fails since 2.3.1.", "claim-3", ["2.2.0", "2.3.1"])]
    out, ci, rec = run8(claims)
    assert_forwarded(ci, rec, claims)
    assert out.ie.identified_claims == claims and out.ie.no_checkable_claims is False
    assert [r.claim_id for r in out.ci_results] == ["claim-1", "claim-2", "claim-3"]


def test_IF_8_one_named_version():
    """Section 7: "... one named version ..." (the version list reaches CI unchanged)."""
    claims = [claim_in(BODY8, "Save fails with Error E42 in 2.3.1.", "claim-1", ["2.3.1"])]
    _, ci, rec = run8(claims)
    assert_forwarded(ci, rec, claims)
    assert ci.requests[0].named_project_versions == ["2.3.1"]


def test_IF_8_two_compared_versions_keep_order():
    """Section 7: "... two compared versions ..." (order of first appearance is kept, none added or dropped)."""
    claims = [claim_in(BODY8, "It worked in 2.2.0 but fails since 2.3.1.", "claim-1", ["2.2.0", "2.3.1"])]
    _, ci, rec = run8(claims)
    assert_forwarded(ci, rec, claims)
    assert ci.requests[0].named_project_versions == ["2.2.0", "2.3.1"]


def test_IF_8_no_claims_a6_sends_nothing_to_ci():
    """Section 7: "... no claims (A.6) ..." Explicit no-claims result: zero CI requests, and the maintainer is told."""
    ci, ie = RecordingCI(), Recorder(lambda r: result_for(r, "A.6"))
    out = pipeline.run(EX["A.2"]["raw_body"], "paste", title=EX["A.2"]["title"], evaluator=ie, investigator=ci)
    assert ci.requests == [] and out.ci_results == []
    assert out.ie.no_checkable_claims is True and out.ie.identified_claims == []
    assert any("No checkable claim" in x for x in out.could_not_check)


@pytest.mark.parametrize("status, n_claims", [("partial", 2), ("partial", 0), ("not_performed", 0)])
def test_IF_8_interrupted_extraction(status, n_claims):
    """Section 7: "... and interrupted extraction." (claim_extraction not completed: the claims found so far, if any,
    are forwarded untouched, nothing is invented, and the maintainer is told extraction was not complete.)"""
    claims = [claim_in(BODY8, "Save fails with Error E42 in 2.3.1.", "claim-1", ["2.3.1"]),
              claim_in(BODY8, "Open `main.py` and call `save()`.", "claim-2")][:n_claims]
    err = {"severity": "error", "code": "internal_error", "path": None, "message": "extraction interrupted"}
    out, ci, rec = run8(claims, processing_status="partial", claim_extraction=IEClaimExtraction(status=status, reason="interrupted"),
                        no_checkable_claims=False if claims else None, diagnostics=[IEDiagnostic(**err)])
    assert_forwarded(ci, rec, claims)
    assert out.ie.no_checkable_claims is (False if claims else None)  # false if claims were found, never "no claims"
    assert any(f"Claim extraction {status}: interrupted" in x for x in out.could_not_check)


def test_IF_8_a_ci_failure_for_one_claim_does_not_drop_the_others():
    """Section 7: "Integration checks forwarding." Every claim is still sent when CI fails on one of them."""
    claims = [claim_in(BODY8, "Save fails with Error E42 in 2.3.1.", "claim-1"),
              claim_in(BODY8, "Open `main.py` and call `save()`.", "claim-2")]
    seen = []

    class Flaky:
        def investigate(self, request):
            seen.append(request.claim_id)
            if request.claim_id == "claim-1":
                raise RuntimeError("down")
            return ci_result(request)
    out = pipeline.run(BODY8, "paste", evaluator=Recorder(lambda r: ie_result(r, claims=claims)), investigator=Flaky())
    assert seen == ["claim-1", "claim-2"] and [r.claim_id for r in out.ci_results] == ["claim-2"]
    assert any("claim-1" in x or "Save fails" in x for x in out.could_not_check)


# --- IF-10 ------------------------------------------------------------------------------------

@pytest.mark.parametrize("label, source, make", [
    ("A.5", "A.1", lambda r: result_for(r, "A.5")),
    ("A.6", "A.2", lambda r: result_for(r, "A.6")),
    ("partial", "A.1", a5_partial)])
def test_IF_10_integration_forwards_what_it_received(label, source, make):
    """Section 7: "Send results A.5, A.6, and a partial result through Integration and compare what it forwards
    with what it received." (Deep equality of the IE result in MaintainerOutput.ie, of its JSON, and of every
    CI request against the claims received.)"""
    ex = EX[source]
    sent, ci = {}, RecordingCI()

    def evaluator(record):
        sent["ie"] = make(record)
        sent["copy"] = copy.deepcopy(sent["ie"])  # what it received, frozen before Integration touches it
        return sent["ie"]
    out = pipeline.run(ex["raw_body"], "paste", title=ex["title"], evaluator=Recorder(evaluator), investigator=ci)
    assert out.ie == sent["copy"] and out.ie.model_dump() == sent["copy"].model_dump()
    assert out.ie.model_dump_json() == sent["copy"].model_dump_json()
    assert [f.model_dump() for f in out.ie.criterion_findings] == [f.model_dump() for f in sent["copy"].criterion_findings]
    assert out.ie.unevaluated_criteria == sent["copy"].unevaluated_criteria
    assert out.ie.identified_claims == sent["copy"].identified_claims
    assert out.ie.provenance == sent["copy"].provenance and out.ie.diagnostics == sent["copy"].diagnostics
    claims = sent["copy"].identified_claims
    assert len(ci.requests) == len(claims) == len(out.ci_results)
    for req, claim in zip(ci.requests, claims):
        assert (req.claim_id, req.claim_text, req.source, req.relevant_context, req.named_project_versions) == (
            claim.claim_id, claim.claim_text, claim.source, claim.relevant_context, claim.named_project_versions)
    if label == "partial":
        assert out.ie.unevaluated_criteria == ["C6"] and out.ie.criterion_findings[5].rating is None
    if label == "A.6":
        assert claims == [] and ci.requests == []


# --- IF-11 ------------------------------------------------------------------------------------

def malformed():
    ok = lambda r: json.loads(ie_result(r).model_dump_json())
    return {
        "missing_field": lambda r: {k: v for k, v in ok(r).items() if k != "provenance"},
        "unknown_field": lambda r: {**ok(r), "surprise": 1},
        "bad_schema_version": lambda r: {**ok(r), "schema_version": "2.0"},
        "bad_type": lambda r: {**ok(r), "criterion_findings": "none"},
        "bad_rating": lambda r: {**ok(r), "criterion_findings": [{**f, "rating": "X"} for f in ok(r)["criterion_findings"]]},
        "not_an_object": lambda r: ["a", "list"],
        "none": lambda r: None,
        "raises": lambda r: (_ for _ in ()).throw(TimeoutError("no answer")),
    }


@pytest.mark.parametrize("name", list(malformed()))
def test_IF_11_malformed_result_is_reported_as_a_failure(name):
    """Section 7: "... and return a malformed result." (the in-process part: a missing, malformed or failing result is
    a failure, never a success, and nothing is sent to Claim Investigation.)"""
    ci = RecordingCI()
    with pytest.raises(InputEvaluationError, match="Input Evaluation"):
        pipeline.run("The Save dialog shows Error E42.", "paste", evaluator=Recorder(malformed()[name]), investigator=ci)
    assert ci.requests == []


@pytest.mark.parametrize("change", [{"request_id": "req-other"}, {"snapshot_id": "snap-other"}, {"request_id": None}],
                         ids=["other-request", "other-snapshot", "null-id-on-completed"])
def test_IF_11_result_for_another_request_or_snapshot_is_a_failure(change):
    """Section 7: "... and return a malformed result." Matching is by request_id and snapshot_id (draft 4.3); a
    conflicting result is a failure."""
    ci = RecordingCI()
    with pytest.raises(InputEvaluationError, match="another request"):
        pipeline.run("x", "paste", evaluator=Recorder(lambda r: ie_result(r, **change)), investigator=ci)
    assert ci.requests == []


def test_IF_11_resend_after_timeout_with_the_same_id():
    """Section 7: "Resend after timeout with the same ID ..." """
    pytest.skip(PENDING)


def test_IF_11_re_evaluate_with_a_new_id():
    """Section 7: "... re-evaluate with a new ID ..." """
    pytest.skip(PENDING)


def test_IF_11_reuse_an_id_with_changed_content():
    """Section 7: "... reuse an ID with changed content ..." (correlation_conflict) """
    pytest.skip(PENDING)


# --- IF-12 ------------------------------------------------------------------------------------

LOGIN = "octocat-secret"
FORBIDDEN_KEYS = {"user", "login", "author", "reporter", "assignee", "assignees", "email", "avatar_url", "author_association"}


def scan(obj, needle, seen=None, depth=0):
    """True if `needle` is found anywhere inside str/bytes/containers/objects reachable from obj."""
    seen = set() if seen is None else seen
    if id(obj) in seen or depth > 6:
        return False
    seen.add(id(obj))
    if isinstance(obj, str):
        return needle in obj.lower()
    if isinstance(obj, bytes):
        return needle.encode() in obj.lower()
    if isinstance(obj, dict):
        return any(scan(k, needle, seen, depth + 1) or scan(v, needle, seen, depth + 1) for k, v in obj.items())
    if isinstance(obj, (list, tuple, set, frozenset)):
        return any(scan(v, needle, seen, depth + 1) for v in obj)
    if hasattr(obj, "__dict__") and not isinstance(obj, type) and not callable(obj):
        return scan(vars(obj), needle, seen, depth + 1)
    return False


def test_IF_12_three_reports_from_one_reporter_leave_no_identity_or_link(monkeypatch, caplog):
    """Section 7: "Process several reports from the same reporter and inspect both sides' records and logs for
    identity links." (Integration's automated part: three issues whose GitHub `user.login` is identical go through
    the pipeline, the web page and the JSON API; the login must appear in no record, output, CI request, HTML, log
    line or module-level state, no model has an identity field, and nothing links the three reports.)"""
    payloads = [gh_payload(n, title=f"Crash number {n}", body=f"### What happened?\nSave crashes, case {n}.\n")
                for n in (7, 8, 9)]
    assert {p["user"]["login"] for p in payloads} == {LOGIN}
    mock_github(monkeypatch, *payloads)
    caplog.set_level(logging.DEBUG)
    ie = Recorder(lambda r: ie_result(r, claims=[claim_in(r.raw_body, "Save crashes", "c1")]))
    ci = RecordingCI()
    outputs = [run_github(f"https://github.com/o/r/issues/{n}", evaluator=ie, investigator=ci) for n in (7, 8, 9)]
    client = TestClient(app)
    pages = [client.post("/evaluate", data={"issue_url": f"https://github.com/o/r/issues/{n}"}).text for n in (7, 8, 9)]
    apis = [client.post("/api/evaluate", data={"issue_url": f"https://github.com/o/r/issues/{n}"}).json() for n in (7, 8, 9)]
    assert len(outputs) == len(pages) == len(apis) == 3

    needle = LOGIN.lower()
    for out in outputs:
        assert needle not in out.model_dump_json().lower()
        assert not FORBIDDEN_KEYS & set(all_keys(json.loads(out.model_dump_json())))
    for rec in ie.records:
        assert needle not in rec.model_dump_json().lower()
    assert len(ci.requests) == 3 and all(needle not in r.model_dump_json().lower() for r in ci.requests)
    for text in pages:
        assert needle not in text.lower() and "avatars.githubusercontent" not in text
    for api in apis:
        assert needle not in json.dumps(api).lower() and not FORBIDDEN_KEYS & set(all_keys(api))
    assert needle not in caplog.text.lower()
    for name, mod in list(sys.modules.items()):  # module-level state of our own code (and the test's helpers)
        if name.split(".")[0] in ("integration", "input_evaluation", "claim_investigation", "conftest"):
            assert not scan(vars(mod), needle), f"{LOGIN} found in module state of {name}"
    # no model has an identity field
    models = [m for n, m in sys.modules.items() if n == "integration.models"]
    for cls in vars(models[0]).values():
        if isinstance(cls, type) and hasattr(cls, "model_fields"):
            assert not FORBIDDEN_KEYS & set(cls.model_fields), cls.__name__
    # the three records are not linked: distinct ids, no shared value that could identify the reporter
    ids = [(o.record.request_id, o.record.snapshot_id) for o in outputs]
    assert len({i[0] for i in ids}) == 3 and len({i[1] for i in ids}) == 3
    assert len({o.sha256 for o in outputs}) == 3 and len({o.record.issue_url for o in outputs}) == 3

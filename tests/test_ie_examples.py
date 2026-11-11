"""Every example in the IE draft v1 appendix (A.1-A.7, copied to fixtures/ie_examples.json) is accepted or rejected
exactly as the draft intends, and Integration's own output for A.1 equals the draft's record."""
import copy
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from bugs26.integration import intake, route
from bugs26.integration.models import IEFinding, IEReportRecord, IEResult

EX = json.loads((Path(__file__).parent / "fixtures" / "ie_examples.json").read_text(encoding="utf-8"))


def a3():  # "Same as A.2 but with request_id req-003 and the raw_body field removed"
    d = {**EX["A.2"], "request_id": "req-003"}
    del d["raw_body"]
    return d


@pytest.mark.parametrize("name, cls", [("A.1", IEReportRecord), ("A.2", IEReportRecord), ("A.4", IEResult),
                                       ("A.5", IEResult), ("A.6", IEResult), ("A.7", IEFinding)])
def test_draft_examples_are_accepted(name, cls):
    obj = cls.model_validate(EX[name])
    assert json.loads(obj.model_dump_json()) == EX[name]  # nothing dropped or changed (INT-8)


def test_a3_is_rejected():
    with pytest.raises(ValidationError):
        IEReportRecord.model_validate(a3())


@pytest.mark.parametrize("field", ["schema_version", "title", "labels", "sections", "body_source", "repository", "created_at"])
def test_every_record_field_is_required(field):
    d = copy.deepcopy(EX["A.1"])
    del d[field]
    with pytest.raises(ValidationError):
        IEReportRecord.model_validate(d)


@pytest.mark.parametrize("field", ["criterion_findings", "unevaluated_criteria", "identified_claims", "no_checkable_claims",
                                   "diagnostics", "schema_version", "provenance"])
def test_every_result_field_is_required(field):
    d = copy.deepcopy(EX["A.5"])
    del d[field]
    with pytest.raises(ValidationError):
        IEResult.model_validate(d)


def test_other_violations_are_rejected():
    def bad(cls, d, edit):
        d = copy.deepcopy(d)
        edit(d)
        with pytest.raises(ValidationError):
            cls.model_validate(d)
    bad(IEResult, EX["A.5"], lambda d: d["criterion_findings"][0].pop("criteria_version"))
    bad(IEResult, EX["A.5"], lambda d: d["provenance"].update(external_models=[{"x": 1}]))
    bad(IEResult, EX["A.5"], lambda d: d.update(unevaluated_criteria=["C9"]))
    bad(IEResult, EX["A.5"], lambda d: d.update(surprise=1))
    bad(IEResult, EX["A.5"], lambda d: d["criterion_findings"][0].update(evidence=[]))
    bad(IEReportRecord, EX["A.1"], lambda d: d["sections"][0].update(original_label=""))
    bad(IEReportRecord, EX["A.1"], lambda d: d.update(issue_number=-1))
    bad(IEReportRecord, EX["A.1"], lambda d: d["sections"][0].pop("recognition"))


def test_draft_results_pass_the_consistency_check():
    """A.5 and A.6 are completed, A.4 is invalid_input with null ids matched by the call, A.7 is part of a partial result."""
    for name, req in (("A.5", "A.1"), ("A.6", "A.2")):
        raw = intake.receive(EX[req]["raw_body"], "paste", title=EX[req]["title"])
        raw = raw.model_copy(update=dict(request_id=EX[name]["request_id"], snapshot_id=EX[name]["snapshot_id"]))
        route.match_ie(raw, IEResult.model_validate(EX[name]))
    route.match_ie(raw, IEResult.model_validate({**EX["A.4"], "request_id": None, "snapshot_id": None}))
    raw = raw.model_copy(update=dict(request_id="req-003", snapshot_id="snap-124-a"))
    route.match_ie(raw, IEResult.model_validate(EX["A.4"]))
    a5 = copy.deepcopy(EX["A.5"])
    a5["criterion_findings"][5] = EX["A.7"]
    a5.update(processing_status="partial", unevaluated_criteria=["C6"], diagnostics=[
        {"severity": "error", "code": "dependency_unavailable", "path": None, "message": "Evidence-access service unavailable."}])
    raw = intake.receive(EX["A.1"]["raw_body"], "paste", title=EX["A.1"]["title"])  # a5 quotes A.1's text
    raw = raw.model_copy(update=dict(request_id=a5["request_id"], snapshot_id=a5["snapshot_id"]))
    route.match_ie(raw, IEResult.model_validate(a5))


def test_our_record_for_a1_equals_the_draft():
    ex = EX["A.1"]
    raw = intake.receive(ex["raw_body"], "github", "https://github.com/example/editor", ex["title"], ex["issue_url"],
                         issue_number=123, labels=["bug"], created_at=ex["created_at"], updated_at=ex["updated_at"])
    record = intake.to_record(raw, intake.structure(raw)).model_dump(mode="json")
    for k in ("request_id", "snapshot_id", "body_source"):  # ours are new uuids, and "current" (initial text unavailable)
        record.pop(k)
    theirs = {k: v for k, v in ex.items() if k not in ("request_id", "snapshot_id", "body_source")}
    assert record == theirs


def test_a2_free_form_and_a1_structure_agree():
    raw = intake.receive(EX["A.2"]["raw_body"], "paste", title=EX["A.2"]["title"])
    s = intake.structure(raw)
    assert s.sections == [] and json.loads(s.extraction.model_dump_json()) == EX["A.2"]["extraction"]

from pathlib import Path

import pytest

from integration.models import (CIFinding, CIResult, IEClaim, IEClaimExtraction, IEEvidence, IEFinding,
                                       IELines, IEProvenance, IEResult)

SAMPLES = Path(__file__).resolve().parent.parent / "samples"
NAMES = ["good-report.md", "missing-steps.md", "cites-nonexistent-file.md", "issue-form-report.md"]


def sample(name: str) -> str:
    return (SAMPLES / name).read_text(encoding="utf-8")


def ie_evidence(text="e", **kw):
    return IEEvidence(**{"basis": "absence_check", "source": "whole_report", "section_id": None, "lines": None,
                         "quote": None, "explanation": text, **kw})


def ie_claim(n=0, text="load_config()"):  # appears on line 15 of samples/good-report.md
    return IEClaim(claim_id=f"c{n}", claim_text=text, relevant_context=text,
                   source=ie_evidence(basis="quotation", source="raw_body", lines=IELines(start=15, end=15), quote=text),
                   named_project_versions=["1.2"])


def ie_result(record, claims=(), **kw):
    """A valid IE v1 result for a record (7 concluded findings), for fake evaluators."""
    findings = [IEFinding(criterion_id=f"C{i}", criteria_version="v1", evaluation_status="concluded", rating="P",
                          explanation="fine", evidence=[ie_evidence()], unevaluated_reason=None) for i in range(1, 8)]
    base = dict(schema_version="1.0", request_id=record.request_id, snapshot_id=record.snapshot_id, processing_status="completed",
                criterion_findings=findings, claim_extraction=IEClaimExtraction(status="completed", reason=None),
                identified_claims=list(claims), no_checkable_claims=not claims, unevaluated_criteria=[], diagnostics=[],
                provenance=IEProvenance(criteria_version="v1", evaluator_version="fake", external_models=[],
                                        evaluated_at="2026-11-11T00:00:00Z"))
    return IEResult(**{**base, **kw})


def ci_result(request, outcome="supported", limitation=None, n_findings=1):
    findings = [CIFinding(claim_id=request.claim_id, outcome=outcome, explanation="because") for _ in range(n_findings)]
    return CIResult(request_id=request.request_id, claim_id=request.claim_id, findings=findings, limitation=limitation)


@pytest.fixture
def good():
    return sample("good-report.md")


@pytest.fixture(autouse=True)
def supported_repo_o_r(tmp_path, monkeypatch):
    """Tests use the repo o/r; the real supported_repos.txt is tested separately."""
    from integration import github
    f = tmp_path / "supported_repos.txt"
    f.write_text("# test list\no/r\n", encoding="utf-8")
    monkeypatch.setattr(github, "SUPPORTED_FILE", f)

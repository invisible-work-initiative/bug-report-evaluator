"""PLACEHOLDER Input Evaluation. The real IE subsystem (another team) replaces this. Returns the IE draft v1 shape.

It rates a criterion P when a section for it has content, and otherwise leaves it unevaluated: a missing heading
does not mean missing information (IE draft), so the placeholder never says M. It finds code references by regex.
It does not judge quality. Finding claims is IE's job, not Integration's.
"""
import re
from datetime import datetime, timezone

from ..integration.models import (CRITERIA, IEClaim, IEClaimExtraction, IEDiagnostic, IEEvidence, IEFinding, IELines,
                                  IEProvenance, IEReportRecord, IEResult, IESection, IEUnevaluatedReason)

PREFIX = "[PLACEHOLDER Input Evaluation] "
CRITERIA_VERSION = "git:b1820e5:documentation/bug-report-quality-criteria.md"  # commit pinned in the IE draft
CONCEPTS = {"C1": "bug_description", "C2": "steps_to_reproduce", "C3": "expected_behavior", "C4": "observed_behavior",
            "C5": "environment_version"}  # C6 and C7 are never judged

_COMMENT = re.compile(r"<!--.*?(?:-->|\Z)", re.S)
# code references: `token` with a letter and one of . ( _ /  |  path/file.ext[:line]  |  name()
_CODE = re.compile(r"`(?P<tick>[^`\s]+)`"
                   r"|(?P<path>(?:[\w.-]+/)*[\w-]+\.(?:py|js|jsx|ts|tsx|java|c|h|cpp|go|rs|rb|php|cs|kt|json|ya?ml|toml|md|html|css)\b(?::\d+)?)"
                   r"|(?P<call>\b[A-Za-z_][\w.]*\(\))")
_URL = re.compile(r"https?://\S+")


def meaningful_text(section: IESection) -> str:
    """Section value without HTML comments and edge whitespace. Empty = nothing useful was written.
    (IE, not Integration, decides this; "_No response_" is template text.)"""
    text = _COMMENT.sub("", section.value or "").strip()
    return "" if text == "_No response_" else text


def find_code_references(body: str) -> list[tuple[str, int, int]]:
    """Unique (text, start, end), first occurrence, not inside URLs."""
    urls = [m.span() for m in _URL.finditer(body)]
    found = {}
    for m in _CODE.finditer(body):
        kind = m.lastgroup
        start, end = m.span(kind)
        text = body[start:end]
        if kind == "tick" and not (re.search("[A-Za-z]", text) and re.search(r"[._(/]", text)):
            continue
        if not any(a <= start < b for a, b in urls):
            found.setdefault(text, (text, start, end))
    return list(found.values())


class StubInputEvaluator:
    PLACEHOLDER = True

    def evaluate(self, record: IEReportRecord) -> IEResult:
        findings = []
        for cid, name in CRITERIA.items():
            secs = [s for s in record.sections if cid in CONCEPTS and s.semantic_concept == CONCEPTS[cid] and meaningful_text(s)]
            if secs:
                findings.append(IEFinding(
                    criterion_id=cid, criteria_version=CRITERIA_VERSION, evaluation_status="concluded", rating="P",
                    explanation=PREFIX + f"{'An' if name[0] in 'AEIOU' else 'A'} {name.lower()} section is present.",
                    unevaluated_reason=None,
                    evidence=[IEEvidence(basis="quotation", source="raw_body", section_id=s.section_id,
                                         lines=s.source_lines, quote=s.value, explanation=f"Text under '{s.original_label}'.")
                              for s in secs]))
            else:
                why = ("The placeholder reads only sections; a missing heading is not missing information." if cid in CONCEPTS
                       else "The placeholder does not judge this criterion.")
                findings.append(IEFinding(
                    criterion_id=cid, criteria_version=CRITERIA_VERSION, evaluation_status="unevaluated", rating=None,
                    explanation=PREFIX + f"{name} was not evaluated.", unevaluated_reason=IEUnevaluatedReason(
                        code="unsupported_content" if cid in CONCEPTS else "dependency_unavailable", message=f"{cid}: {why}"),
                    evidence=[IEEvidence(basis="source_reference", source="whole_report", section_id=None, lines=None,
                                         quote=None, explanation="Not evaluated by the placeholder.")]))

        body, lines = record.raw_body, record.raw_body.split("\n")
        claims = []
        for n, (text, start, _) in enumerate(find_code_references(body), 1):
            ln = body.count("\n", 0, start) + 1
            section = next((s.section_id for s in record.sections if s.source_lines and s.source_lines.start <= ln <= s.source_lines.end), None)
            claims.append(IEClaim(
                claim_id=f"claim-{n}", claim_text=text, relevant_context=lines[ln - 1].rstrip("\r"),
                named_project_versions=[],
                source=IEEvidence(basis="quotation", source="raw_body", section_id=section,
                                  lines=IELines(start=ln, end=ln), quote=text,
                                  explanation="Code reference found in the text (placeholder regex).")))

        unevaluated = [f for f in findings if f.evaluation_status == "unevaluated"]
        diagnostics = [IEDiagnostic(severity="error", code=f.unevaluated_reason.code, path=None,
                                    message=f.unevaluated_reason.message) for f in unevaluated]
        if record.body_source == "current":
            diagnostics.append(IEDiagnostic(severity="warning", code="not_initial_submission", path="/body_source",
                                            message="The text is the current text; later edits may be included."))
        return IEResult(
            schema_version="1.0", request_id=record.request_id, snapshot_id=record.snapshot_id,
            processing_status="partial" if unevaluated else "completed",
            criterion_findings=findings, unevaluated_criteria=[f.criterion_id for f in unevaluated],
            claim_extraction=IEClaimExtraction(status="completed", reason=None),
            identified_claims=claims, no_checkable_claims=not claims, diagnostics=diagnostics,
            provenance=IEProvenance(criteria_version=CRITERIA_VERSION, evaluator_version="placeholder-ie/0",
                                    external_models=[],
                                    evaluated_at=datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")))

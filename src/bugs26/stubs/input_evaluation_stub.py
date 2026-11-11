"""PLACEHOLDER Input Evaluation. The real IE subsystem (another team) replaces this. Returns the IE draft v1 shape.

It only checks whether each section exists (P / M, or unevaluated) and finds code references by regex.
It does not judge quality. Finding claims is IE's job, not Integration's.
"""
import re
from datetime import datetime, timezone

from ..integration.models import (IEClaim, IEClaimExtraction, IEDiagnostic, IEEvidence, IEFinding, IELines,
                                  IEProvenance, IEReportRecord, IEResult, IESection, IEUnevaluatedReason)

PLACEHOLDER = "[PLACEHOLDER Input Evaluation] "
CRITERIA_VERSION = "git:b1820e5:documentation/bug-report-quality-criteria.md"  # commit pinned in the IE draft
CRITERIA = [  # (id, section concept, name)
    ("C1", "bug_description", "bug description"),
    ("C2", "steps_to_reproduce", "steps to reproduce"),
    ("C3", "expected_behavior", "expected behavior"),
    ("C4", "observed_behavior", "observed behavior"),
    ("C5", "environment_version", "environment and version"),
]
UNJUDGED = [("C6", "supporting evidence"), ("C7", "clarity and specificity")]

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
    def evaluate(self, record: IEReportRecord) -> IEResult:
        findings = []

        def add(cid, rating, text, evidence, reason=None):
            findings.append(IEFinding(
                criterion_id=cid, criteria_version=CRITERIA_VERSION,
                evaluation_status="concluded" if rating else "unevaluated", rating=rating,
                explanation=PLACEHOLDER + text, evidence=evidence, unevaluated_reason=reason))

        whole = lambda text: IEEvidence(basis="absence_check", source="whole_report", explanation=text)
        for cid, concept, name in CRITERIA:
            secs = [s for s in record.sections if s.semantic_concept == concept and meaningful_text(s)]
            if secs:
                add(cid, "P", f"A {name} section is present.",
                    [IEEvidence(basis="quotation", source="raw_body", section_id=s.section_id,
                                lines=s.source_lines, quote=s.value, explanation=f"Text under '{s.original_label}'.")
                     for s in secs])
            elif record.extraction.mode == "free_form":
                add(cid, None, "Free-form report: the placeholder only reads sections.",
                    [IEEvidence(basis="source_reference", source="whole_report",
                                explanation="The placeholder cannot read a report without sections.")],
                    IEUnevaluatedReason(code="unsupported_content", message="Free-form report (no sections); the placeholder cannot evaluate it."))
            else:
                add(cid, "M", f"No {name} section with content was found.", [whole(f"Looked for a {name} section; none has content.")])
        for cid, name in UNJUDGED:
            add(cid, None, f"{name} is not judged by the placeholder.",
                [IEEvidence(basis="source_reference", source="whole_report", explanation="Not judged.")],
                IEUnevaluatedReason(code="dependency_unavailable", message=f"{cid} ({name}) is not judged by the placeholder."))

        body, lines = record.raw_body, record.raw_body.split("\n")
        claims = []
        for n, (text, start, _) in enumerate(find_code_references(body), 1):
            ln = body.count("\n", 0, start) + 1
            section = next((s.section_id for s in record.sections if s.source_lines and s.source_lines.start <= ln <= s.source_lines.end), None)
            claims.append(IEClaim(
                claim_id=f"claim-{n}", claim_text=text, relevant_context=lines[ln - 1].rstrip("\r"),
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
            request_id=record.request_id, snapshot_id=record.snapshot_id,
            processing_status="partial" if unevaluated else "completed",
            criterion_findings=findings, unevaluated_criteria=[f.criterion_id for f in unevaluated],
            claim_extraction=IEClaimExtraction(status="completed"),
            identified_claims=claims, no_checkable_claims=not claims, diagnostics=diagnostics,
            provenance=IEProvenance(criteria_version=CRITERIA_VERSION, evaluator_version="placeholder-ie/0",
                                    evaluated_at=datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")))

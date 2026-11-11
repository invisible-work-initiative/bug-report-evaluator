"""PLACEHOLDER Input Evaluation. The real IE subsystem (another team) replaces this.

It only checks whether each section exists (present / not found / unable to judge) and finds
code references by regex. It does not judge quality. Finding claims is IE's job, not Integration's.
"""
import re

from ..integration.intake import meaningful_text
from ..integration.models import Evidence, Finding, IEResult, InvestigationRequest, RawReport, StructuredReport

PLACEHOLDER = "[PLACEHOLDER Input Evaluation] "
CRITERIA = [  # (id, structured field, name)
    ("C1", "description", "description"),
    ("C2", "steps_to_reproduce", "steps to reproduce"),
    ("C3", "expected_behavior", "expected behavior"),
    ("C4", "observed_behavior", "observed behavior"),
    ("C5", "environment", "environment"),
]
UNJUDGED = [("C6", "evidence"), ("C7", "clarity")]

# code references: `token` with a letter and one of . ( _ /  |  path/file.ext[:line]  |  name()
_CODE = re.compile(r"`(?P<tick>[^`\s]+)`"
                   r"|(?P<path>(?:[\w.-]+/)*[\w-]+\.(?:py|js|jsx|ts|tsx|java|c|h|cpp|go|rs|rb|php|cs|kt|json|ya?ml|toml|md|html|css)\b(?::\d+)?)"
                   r"|(?P<call>\b[A-Za-z_][\w.]*\(\))")
_URL = re.compile(r"https?://\S+")


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
    def evaluate(self, raw: RawReport, structured: StructuredReport) -> IEResult:
        rid, findings, present = raw.report_id, [], set()

        def add(cid, name, status, text, evidence):
            findings.append(Finding(finding_id=f"{rid}-{cid}", report_id=rid, source="input_evaluation",
                                    subject=f"{cid} {name}", status=status, statement=PLACEHOLDER + text,
                                    evidence=evidence))
        for cid, field, name in CRITERIA:
            sections = [s for s in structured.fields.get(field, []) if meaningful_text(s)]
            if sections:
                present.add(cid)
                add(cid, name, "present", f"A {name} section is present.",
                    [Evidence(kind="report_excerpt", ref=f"report:{rid}", excerpt=s.text, start=s.start, end=s.end)
                     for s in sections])
            else:
                add(cid, name, "not_found", f"No {name} section was found.",
                    [Evidence(kind="note", ref=f"report:{rid}", excerpt="no matching section")])
        for cid, name in UNJUDGED:
            add(cid, name, "unable_to_judge", f"{name} is not judged by the placeholder.",
                [Evidence(kind="note", ref=f"report:{rid}", excerpt="not judged")])

        missing = [name for cid, _, name in CRITERIA if cid in ("C2", "C3", "C4") and cid not in present]
        refs = find_code_references(raw.original_body)
        if "C2" in present and ({"C3", "C4"} & present) and refs:
            decision, reason = "investigate", "Steps, expected or observed behavior, and code references are present."
        elif missing:
            decision, reason = "request_more_information", "Missing: " + ", ".join(missing) + "."
        else:
            decision, reason = "do_not_investigate", "No checkable claim: the report cites no code references."
        requests = [InvestigationRequest(claim_id=f"{rid}-claim-{n}", report_id=rid, claim_text=text,
                                         location={"start": start, "end": end},
                                         ie_context={"origin": "placeholder IE: code reference found in text"})
                    for n, (text, start, end) in enumerate(refs, 1)] if decision == "investigate" else []
        return IEResult(report_id=rid, decision=decision, reason=reason, missing_information=missing,
                        findings=findings, investigation_requests=requests,
                        not_checked=["C6/C7 not judged (placeholder)",
                                     "Content quality not judged - only section presence (placeholder)"])

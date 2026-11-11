"""Intake: receive (INT-1), structure (INT-2) and check (FMEA F.1) a bug report. Nothing is stored (INT-9)."""
import hashlib
import re
import uuid
from datetime import datetime, timezone
from typing import Optional

from .models import IEExtraction, IEExtractionDiagnostic, IELines, IEReportRecord, IESection, RawReport, StructuredReport


class PreparationError(ValueError):
    """The report could not be prepared faithfully; the run must stop (no fake result)."""


class InputEvaluationError(Exception):
    """Input Evaluation raised. The run stops: without IE there is no honest result."""


def receive(body: str, source: str, repo_url: Optional[str] = None, title: Optional[str] = None,
            issue_url: Optional[str] = None, *, issue_number: Optional[int] = None, labels: Optional[list] = None,
            created_at: Optional[str] = None, updated_at: Optional[str] = None) -> RawReport:
    """INT-1: keep title and body verbatim; an empty body is valid. Missing GitHub fields stay None (never made up).
    body_source is always "current": the initial text is not available."""
    title = title or ""
    return RawReport(
        request_id=str(uuid.uuid4()), snapshot_id=str(uuid.uuid4()),
        sha256=hashlib.sha256((title + "\n" + body).encode("utf-8")).hexdigest(),
        received_at=datetime.now(timezone.utc), source=source,
        repository="/".join(repo_url.rstrip("/").split("/")[-2:]) if repo_url else None,
        issue_number=issue_number, issue_url=issue_url or None, title=title, raw_body=body,
        labels=labels or [], created_at=created_at, updated_at=updated_at,
    )


def to_record(raw: RawReport, structured: StructuredReport) -> IEReportRecord:
    """INT-3: the one record sent to IE: the original (raw_body) and the structured sections."""
    return IEReportRecord(schema_version="1.0", **raw.model_dump(exclude={"sha256", "received_at", "source"}),
                          sections=structured.sections, extraction=structured.extraction)


# --- labels -----------------------------------------------------------------------------------

_ALIASES = {
    "bug_description": ["describe the bug", "bug description", "issue description", "what is the issue", "description", "summary"],
    "steps_to_reproduce": ["steps to reproduce", "to reproduce", "reproduction steps", "repro steps",
                           "how to reproduce", "how can we reproduce", "how do we reproduce",
                           "reproducible example", "steps"],
    "expected_behavior": ["expected behavior", "expected behaviour", "expected result", "expected results",
                          "what did you expect", "expected"],
    "observed_behavior": ["actual behavior", "actual behaviour", "actual result", "actual results",
                          "observed behavior", "observed behaviour", "current behavior", "current behaviour",
                          "actual", "observed",
                          "what happened instead", "what happened"],
    "supporting_evidence": ["supporting evidence", "evidence", "screenshots", "logs", "log output", "additional context"],
    "environment_version": ["environment", "desktop", "smartphone", "system info", "system information",
                    "installed versions", "os version", "os environment", "provide environment information",
                    "version", "versions", "platform"],
}


def _normalize(label: str) -> str:
    """Lowercase; drop punctuation, markdown marks and emoji; collapse whitespace."""
    return " ".join(re.sub(r"[^\w\s]|_", " ", label.lower()).split())


def field_for(label: str) -> Optional[str]:
    """Exact alias, alias as a whole-word prefix, or (multi-word aliases, plus version/versions) whole-word suffix.
    Longest alias wins. Never a mid-word substring match."""
    norm = _normalize(label)
    best, best_len = None, 0
    for field, aliases in _ALIASES.items():
        for alias in aliases:
            hit = norm == alias or norm.startswith(alias + " ") or ((" " in alias or alias in ("version", "versions")) and norm.endswith(" " + alias))
            if hit and len(alias) > best_len:
                best, best_len = field, len(alias)
    return best


# --- structure --------------------------------------------------------------------------------

_HEADING = re.compile(r"^ {0,3}#{1,6}[ \t]+(?P<label>.*?)(?:[ \t]+#+)?[ \t]*$")
_BOLD = re.compile(r"^ {0,3}\*\*[ \t]*(?P<label>[^*]+?)[ \t]*(?P<c1>:?)[ \t]*\*\*[ \t]*(?P<c2>:?)[ \t]*(?P<rest>.*)$")
_FENCE = re.compile(r"^ {0,3}(?P<fence>`{3,}|~{3,})(?P<info>.*)$")


def _trim(body: str, start: int, end: int) -> tuple[int, int]:
    """Strip whitespace at the edges by moving the span, never by altering text."""
    while start < end and body[start].isspace():
        start += 1
    while end > start and body[end - 1].isspace():
        end -= 1
    return start, end


def _markers(body: str) -> list[dict]:
    """Find section markers outside fenced code and HTML comments. Each: line_start, value_start, label, field."""
    markers, pos, fence, in_comment = [], 0, None, False
    for line in body.splitlines(keepends=True):
        text = line.rstrip("\r\n\x0b\x0c\x1c\x1d\x1e\x85  ")
        f = _FENCE.match(text)
        if in_comment:
            if "-->" in text:
                in_comment = text.rfind("<!--") > text.rfind("-->")
        elif fence:
            if f and f.group("fence")[0] == fence[0] and len(f.group("fence")) >= len(fence) and not f.group("info").strip():
                fence = None  # closing fence: same char, at least as long
        elif f:
            fence = f.group("fence")
        else:
            m = _marker(text, pos)
            if m:
                markers.append(m)
            in_comment = text.rfind("<!--") > text.rfind("-->")
        pos += len(line)
    return markers


def _marker(text: str, pos: int):
    """Marker dict if this line starts a section, else None."""
    h, b = _HEADING.match(text), _BOLD.match(text)
    end = pos + len(text)
    if h:
        label, value_start = h.group("label"), end
        if not label.strip():
            return None
        before, colon, _ = label.partition(":")
        if colon and field_for(before):  # "## Expected: it should save" -> text after the colon is content
            label, value_start = before.strip(), pos + h.start("label") + len(before) + 1
        return dict(line_start=pos, line_end=end, value_start=value_start, label=label, field=field_for(label))
    if b and field_for(b.group("label")):  # bold only counts for known labels
        if b.group("rest").strip() and not (b.group("c1") or b.group("c2")):
            return None  # "**Expected** it to open..." is a sentence, not a label
        return dict(line_start=pos, line_end=end, value_start=pos + b.start("rest"), label=b.group("label"),
                    field=field_for(b.group("label")))
    return None


def _line(body: str, offset: int) -> int:
    """1-based line number of a character offset: lines split on LF only (IE draft), a CRLF is one break."""
    return body.count("\n", 0, offset) + 1


def _after_eol(body: str, i: int) -> int:
    """Skip one line break at i (the end of a heading line), so the value does not start with it."""
    return i + (2 if body.startswith("\r\n", i) else 1 if body[i:i + 1] in ("\r", "\n") else 0)


def structure(raw: RawReport) -> StructuredReport:
    """INT-2: one IE Section per heading, each value an exact slice of the body (offsets in `spans`). No headings =
    free-form: sections []. Text before the first heading stays in raw_body only. "provided" values are trimmed by
    moving the span; "blank" values keep the exact whitespace."""
    body = raw.raw_body
    markers = _markers(body)
    sections, spans = [], {}
    for i, m in enumerate(markers):
        region_end = markers[i + 1]["line_start"] if i + 1 < len(markers) else len(body)
        start = min(_after_eol(body, m["value_start"]) if m["value_start"] == m["line_end"] else m["value_start"], region_end)
        end = region_end
        provided = bool(body[start:end].strip())
        if provided:
            start, end = _trim(body, start, end)
        sid, first = f"s{i + 1}", _line(body, m["line_start"])
        sections.append(IESection(
            section_id=sid, field_id=None, required=None, original_label=m["label"], status="provided" if provided else "blank",
            value=body[start:end], recognition="recognized" if m["field"] else "unrecognized",
            semantic_concept=m["field"],
            source_lines=IELines(start=first, end=max(first, _line(body, end - 1) if end > start else _line(body, end) if end == len(body) else first))))
        spans[sid] = (start, end)

    mode = "free_form" if not markers else "unsupported_template" if all(x.recognition == "unrecognized" for x in sections) else "structured"
    diagnostics = [IEExtractionDiagnostic(code="no_headings_recognised", message="No heading matched a known concept.")]         if mode == "unsupported_template" else []
    return StructuredReport(sections=sections, spans=spans,
                            extraction=IEExtraction(mode=mode, template_id=None, diagnostics=diagnostics))


def verify_structured(raw: RawReport, structured: StructuredReport) -> None:
    """Preparation check (FMEA F.1): every value an exact slice of the original, inside its source_lines, with a
    label on its first line. Raises PreparationError so the run stops instead of showing a wrong result."""
    body, lines = raw.raw_body, raw.raw_body.split("\n")
    for s in structured.sections:
        span, value, sl = structured.spans.get(s.section_id), s.value or "", s.source_lines
        if span is None or not (0 <= span[0] <= span[1] <= len(body)) or body[span[0]:span[1]] != value:
            raise PreparationError(f"Structured text of section {s.section_id} does not match the original report.")
        if (s.status == "provided") != bool(value.strip()) or s.status == "absent":
            raise PreparationError(f"Section {s.section_id} has the wrong status.")
        if sl is None or not 1 <= sl.start <= sl.end <= len(lines) or s.original_label not in lines[sl.start - 1]:
            raise PreparationError(f"Section {s.section_id} has a wrong label or line range.")
        if span[1] > span[0] and not (sl.start <= _line(body, span[0]) and _line(body, span[1] - 1) <= sl.end):
            raise PreparationError(f"Section {s.section_id}: the text is not inside its source_lines.")

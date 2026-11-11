"""Intake: receive (INT-1), structure (INT-2) and check (FMEA F.1) a bug report. Nothing is stored (INT-9)."""
import hashlib
import re
import uuid
from datetime import datetime, timezone
from typing import Optional

from .models import RawReport, Ref, Section, StructuredReport


class PreparationError(ValueError):
    """The report could not be prepared faithfully; the run must stop (no fake result)."""


def receive(body: str, source: str, repo_url: Optional[str] = None,
            title: Optional[str] = None, issue_url: Optional[str] = None) -> RawReport:
    """INT-1: accept a report and keep the original title/body verbatim (nothing normalised)."""
    if not body or not body.strip():
        raise PreparationError("The report body is empty.")
    return RawReport(
        report_id=str(uuid.uuid4()),
        original_title=title,
        original_body=body,
        sha256=hashlib.sha256(((title or "") + "\n" + body).encode("utf-8")).hexdigest(),
        received_at=datetime.now(timezone.utc),
        source=source,
        repo_url=repo_url or None,
        issue_url=issue_url or None,
    )


# --- labels -----------------------------------------------------------------------------------

FIELDS = ["description", "steps_to_reproduce", "expected_behavior", "observed_behavior", "environment"]
_ALIASES = {
    "description": ["describe the bug", "bug description", "description", "summary", "what happened"],
    "steps_to_reproduce": ["steps to reproduce", "to reproduce", "reproduction steps", "repro steps",
                           "how to reproduce", "steps"],
    "expected_behavior": ["expected behavior", "expected behaviour", "expected result", "expected results",
                          "expected"],
    "observed_behavior": ["actual behavior", "actual behaviour", "actual result", "actual results",
                          "observed behavior", "observed behaviour", "actual", "observed",
                          "what happened instead"],
    "environment": ["environment", "desktop", "smartphone", "system info", "system information", "version", "versions", "platform"],
}


def _normalize(label: str) -> str:
    """Lowercase; drop punctuation, markdown marks and emoji; collapse whitespace."""
    return " ".join(re.sub(r"[^\w\s]|_", " ", label.lower()).split())


def field_for(label: str) -> Optional[str]:
    """Exact alias, or alias as a whole-word prefix. Longest alias wins. Never a substring match."""
    norm = _normalize(label)
    best, best_len = None, 0
    for field, aliases in _ALIASES.items():
        for alias in aliases:
            if (norm == alias or norm.startswith(alias + " ")) and len(alias) > best_len:
                best, best_len = field, len(alias)
    return best


# --- structure --------------------------------------------------------------------------------

_HEADING = re.compile(r"^ {0,3}#{1,6}[ \t]+(?P<label>.*?)[ \t]*#*[ \t]*$")
_BOLD = re.compile(r"^ {0,3}\*\*[ \t]*(?P<label>[^*]+?)[ \t]*:?[ \t]*\*\*[ \t]*:?[ \t]*(?P<rest>.*)$")
_FENCE = re.compile(r"^ {0,3}(```|~~~)")


def _trim(body: str, start: int, end: int) -> tuple[int, int]:
    """Strip whitespace at the edges by moving the span, never by altering text."""
    while start < end and body[start].isspace():
        start += 1
    while end > start and body[end - 1].isspace():
        end -= 1
    return start, end


def _markers(body: str) -> list[dict]:
    """Find section markers outside fenced code. Each: line_start, value_start, label, field."""
    markers, pos, fence = [], 0, None
    for line in body.split("\n"):
        text = line.rstrip("\r")
        f = _FENCE.match(text)
        if f:
            fence = None if fence == f.group(1) else (fence or f.group(1))
        elif fence is None:
            h, b = _HEADING.match(text), _BOLD.match(text)
            if h:
                markers.append(dict(line_start=pos, value_start=pos + len(text), label=h.group("label"),
                                    field=field_for(h.group("label"))))
            elif b and field_for(b.group("label")):  # bold only counts for known labels
                markers.append(dict(line_start=pos, value_start=pos + b.start("rest"), label=b.group("label"),
                                    field=field_for(b.group("label"))))
        pos += len(line) + 1
    return markers


_EXT = "py|js|jsx|ts|tsx|java|c|h|cpp|go|rs|rb|php|cs|kt|swift|json|ya?ml|toml|md|html|css"
_CODE = re.compile(
    rf"`(?P<tick>[\w.]+(?:\(\))?)`"                       # `identifier` or `name()`
    rf"|(?P<path>(?:[\w.-]+/)*[\w-]+\.(?:{_EXT})\b(?::\d+)?)"  # foo/bar.py, a.js:42
    rf"|(?P<call>\b[A-Za-z_][\w.]*\(\))")                  # name()
_VERSION = re.compile(r"(?<![\w.])v?\d+\.\d+\.\d+(?![\w]|\.\d)")
_URL = re.compile(r"https?://\S+")


def _find_refs(body: str, regex, group=None) -> list[Ref]:
    """Unique matches (by text, first occurrence), skipping anything inside a URL."""
    urls = [m.span() for m in _URL.finditer(body)]
    refs, seen = [], set()
    for m in regex.finditer(body):
        name = next((g for g in (group or [None]) if g and m.group(g)), None)
        start, end = m.span(name) if name else m.span()
        if any(u0 <= start < u1 for u0, u1 in urls) or body[start:end] in seen:
            continue
        seen.add(body[start:end])
        refs.append(Ref(text=body[start:end], start=start, end=end))
    return refs


def structure(raw: RawReport) -> StructuredReport:
    """INT-2: split the body into sections. Each Section is an exact slice (start/end) of the body."""
    body = raw.original_body
    markers = _markers(body)
    title = raw.original_title

    # No title given: use the first line if it is a heading that is not a known section.
    if title is None and markers:
        first = markers[0]
        if not body[: first["line_start"]].strip() and first["field"] is None:
            title = first["label"] or None
            first["label"] = None  # the title is not a section; the text after it is plain preamble

    pieces = []  # (label, field, start, end)
    first_start = markers[0]["line_start"] if markers else len(body)
    pieces.append((None, None, 0, first_start))
    for i, m in enumerate(markers):
        end = markers[i + 1]["line_start"] if i + 1 < len(markers) else len(body)
        pieces.append((m["label"], m["field"], m["value_start"], end))

    fields: dict[str, list[Section]] = {}
    unmapped: list[Section] = []
    for label, field, start, end in pieces:
        start, end = _trim(body, start, end)
        if start == end:
            continue
        section = Section(label=label or None, text=body[start:end], start=start, end=end)
        (fields.setdefault(field, []) if field else unmapped).append(section)

    return StructuredReport(
        report_id=raw.report_id,
        title=title,
        fields=fields,
        unmapped=unmapped,
        code_references=_find_refs(body, _CODE, ["tick", "path", "call"]),
        versions=_find_refs(body, _VERSION),
    )


def verify_structured(raw: RawReport, structured: StructuredReport) -> None:
    """Preparation check (FMEA F.1): every span must be an exact slice of the original.
    Raises PreparationError so the run stops instead of showing a wrong result."""
    body = raw.original_body
    if not body.strip():
        raise PreparationError("The report body is empty.")
    if structured.report_id != raw.report_id:
        raise PreparationError("Structured report belongs to a different report.")
    spans = [s for secs in structured.fields.values() for s in secs] + structured.unmapped
    spans += structured.code_references + structured.versions
    for s in spans:
        if not (0 <= s.start <= s.end <= len(body)) or body[s.start:s.end] != s.text:
            raise PreparationError(f"Structured text at {s.start}-{s.end} does not match the original report.")
    t = structured.title
    if t is not None and t != raw.original_title and t not in body:
        raise PreparationError("Title does not match the original report.")

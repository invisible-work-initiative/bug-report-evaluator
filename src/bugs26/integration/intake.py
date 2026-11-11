"""Intake: receive (INT-1) and structure (INT-2) a bug report. Nothing is stored (INT-9)."""
import hashlib
import re
import uuid
from datetime import datetime, timezone
from typing import Optional

from .models import RawReport, StructuredReport


def receive(text: str, source: str, repo_url: Optional[str] = None) -> RawReport:
    """INT-1: accept a report and keep the original text verbatim."""
    if not text or not text.strip():
        raise ValueError("report text is empty")
    return RawReport(
        report_id=str(uuid.uuid4()),
        original_text=text,
        sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
        received_at=datetime.now(timezone.utc),
        source=source,
        repo_url=repo_url or None,
    )


# Words that identify a section label, checked in order.
_LABELS = [
    ("steps_to_reproduce", ("steps to reproduce", "reproduction", "repro steps", "how to reproduce", "steps")),
    ("expected_behavior", ("expected",)),
    ("observed_behavior", ("actual", "observed", "current behavior", "current behaviour")),
    ("environment", ("environment", "version", "system", "platform")),
    ("description", ("description", "summary", "problem", "what happened")),
]

# "## Heading"   or   "**Label:** optional inline text"   or   "Label:" on its own line
_HEADING = re.compile(r"^[ \t]*#{1,6}[ \t]+(?P<label>.+?)[ \t#]*$")
_BOLD = re.compile(r"^[ \t]*\*\*(?P<label>[^*\n]+?)\*\*[ \t]*:?[ \t]*(?P<rest>.*)$")
_PLAIN = re.compile(r"^(?P<label>[A-Za-z][A-Za-z /]{2,40}):[ \t]*$")

_PATH = re.compile(
    r"(?<![\w/.-])(?:[\w.-]+/)*[\w-]+\.(?:py|js|jsx|ts|tsx|java|c|h|cpp|go|rs|rb|php|cs|kt|swift|json|ya?ml|toml|md|html|css)\b(?::\d+)?")
_BACKTICK = re.compile(r"`([\w.]+(?:\(\))?)`")
_CALL = re.compile(r"\b[A-Za-z_][\w.]*\(\)")
_VERSION = re.compile(r"\bv?\d+\.\d+\.\d+\b")


def _field_for(label: str) -> Optional[str]:
    label = label.strip().rstrip(":").lower()
    for field, words in _LABELS:
        if any(w in label for w in words):
            return field
    return None


def _find_markers(text: str) -> list[tuple[int, int, Optional[str]]]:
    """Return (line_start, value_start, field) for each heading-like line."""
    markers = []
    pos = 0
    for line in text.splitlines(keepends=True):
        body = line.rstrip("\r\n")
        m = _HEADING.match(body)
        b = _BOLD.match(body)
        p = _PLAIN.match(body)
        if m:
            markers.append((pos, pos + len(body), _field_for(m.group("label"))))
        elif b:
            # "**Label:** text" -> the colon may be inside or outside the bold markers
            label = b.group("label")
            markers.append((pos, pos + b.start("rest"), _field_for(label)))
        elif p and _field_for(p.group("label")):
            markers.append((pos, pos + len(body), _field_for(p.group("label"))))
        pos += len(line)
    return markers


def _unique(items):
    seen = []
    for i in items:
        if i not in seen:
            seen.append(i)
    return seen


def structure(raw: RawReport) -> StructuredReport:
    """INT-2: split the report into fields. Values are exact substrings of the original;
    anything not present stays None / []. Nothing is invented."""
    text = raw.original_text
    markers = _find_markers(text)
    fields: dict[str, Optional[str]] = {}
    for i, (_, value_start, field) in enumerate(markers):
        end = markers[i + 1][0] if i + 1 < len(markers) else len(text)
        value = text[value_start:end].strip()
        if field and value and field not in fields:
            fields[field] = value

    # Title: first "#" heading that is not a section label, else first non-empty line.
    title = None
    for line_start, value_start, field in markers:
        line = text[line_start:value_start]
        if field is None and line.lstrip().startswith("#"):
            title = line.strip().lstrip("#").strip()
            break
    if not title:
        for line in text.splitlines():
            if line.strip():
                title = line.strip()
                break

    refs = _PATH.findall(text) + _BACKTICK.findall(text) + _CALL.findall(text)
    return StructuredReport(
        report_id=raw.report_id,
        title=title or None,
        code_references=_unique(refs),
        versions=_unique(_VERSION.findall(text)),
        **fields,
    )

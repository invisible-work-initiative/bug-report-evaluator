"""Maintainer-facing web interface (INT-6). Nothing is stored; report text is never logged (INT-9)."""
import re
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException

from . import github, pipeline
from .intake import InputEvaluationError
from .models import CRITERIA

MAX_BYTES = 200 * 1024        # one report
MAX_REQUEST = 256 * 1024      # whole request (Content-Length)
SAMPLES = Path(__file__).resolve().parents[2] / "samples"
_FILE_CLAIM = re.compile(
    r"\.(?:py|js|jsx|ts|tsx|java|c|h|cpp|go|rs|rb|php|cs|kt|json|ya?ml|toml|md|html|css|vault)(?::\d+)?$",
    re.I)

app = FastAPI(title="Bug report evaluator (Integration prototype)")
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


def short(text: Optional[str]) -> str:
    """Evidence excerpt for the table: at most 3 lines and about 200 characters."""
    text = text or ""
    cut = "".join(text.splitlines(True)[:3])[:200]
    return cut + ("..." if cut != text else "")


def _title_section(section) -> bool:
    """A markdown title stored as an empty unrecognized section. It is the page heading, not a field."""
    return section.recognition == "unrecognized" and section.status == "blank" and not (section.value or "").strip()


def display_title(record) -> str:
    if record.title:
        return record.title
    for section in record.sections:
        if _title_section(section) and section.original_label:
            return section.original_label
    described = section_by_concept(record, "bug_description")
    if described and (described.value or "").strip():
        for line in described.value.splitlines():
            text = line.strip().strip("`")
            if text and not text.startswith("```"):
                return text[:120]
    for line in record.raw_body.splitlines():
        text = line.strip()
        if text and not text.startswith("#"):
            return text[:120]
    return "Bug report"


def body_sections(record):
    return [section for section in record.sections if not _title_section(section)]


def section_by_concept(record, concept):
    for section in record.sections:
        if section.semantic_concept == concept and section.recognition == "recognized" and section.status == "provided":
            return section
    return None


def environment_line(record) -> str:
    parts = []
    for section in record.sections:
        if section.semantic_concept == "environment_version" and section.status == "provided" and (section.value or "").strip():
            parts.append(" ".join(short(section.value).split()))
    return " · ".join(part for part in parts if part)


def gap_lines(output) -> list[str]:
    concepts = {section.semantic_concept for section in output.record.sections
                if section.recognition == "recognized" and section.status == "provided"}
    lines = []
    if "steps_to_reproduce" not in concepts:
        lines.append("No steps to reproduce.")
    if not output.ie.identified_claims:
        lines.append("No code reference to check.")
    return lines


def claim_kind(text: str) -> str:
    if text.rstrip().endswith("()"):
        return "call"
    if _FILE_CLAIM.search(text):
        return "file"
    return "other"


def split_limits(items):
    """Separate checks the report itself does not support from checks a placeholder has not run."""
    report, pending = [], []
    for item in items:
        low = item.lower()
        if "placeholder" in low or "notimplementederror" in low or "not connected" in low:
            pending.append(item)
        else:
            report.append(item)
    return {"report": report, "pending": pending}


templates.env.filters["short"] = short
templates.env.globals.update(
    CRITERIA=CRITERIA, display_title=display_title, body_sections=body_sections,
    section_by_concept=section_by_concept, environment_line=environment_line, gap_lines=gap_lines,
    claim_kind=claim_kind, split_limits=split_limits)


@app.exception_handler(StarletteHTTPException)
async def http_error(request: Request, exc: StarletteHTTPException):
    """/evaluate shows an HTML error page; everything else gets JSON."""
    if request.url.path == "/evaluate":
        return templates.TemplateResponse(request, "error.html", {"message": exc.detail}, status_code=exc.status_code)
    return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)


@app.middleware("http")
async def limit_size(request: Request, call_next):
    """Reject oversized requests before the body is parsed."""
    length = request.headers.get("content-length", "")
    if length.isdigit() and int(length) > MAX_REQUEST:
        return await http_error(request, StarletteHTTPException(413, "Request is larger than 256 KB."))
    return await call_next(request)


def _evaluate(text: str, file: Optional[UploadFile], issue_url: str, repo_url: str):
    """Pick exactly one source (paste / upload / GitHub issue) and run the pipeline."""
    upload = b""
    if file is not None and file.filename:
        if not file.filename.lower().endswith((".md", ".txt")):
            raise HTTPException(400, "Only .md or .txt files are accepted.")
        upload = file.file.read(MAX_BYTES + 1)  # an empty upload is ignored
    if sum([bool(text.strip()), bool(upload), bool(issue_url.strip())]) != 1:
        raise HTTPException(400, "Provide exactly one of: pasted text, an uploaded file, or a GitHub issue URL.")
    title, issue, source, meta = None, None, "paste", {}
    try:
        if repo_url.strip() and not issue_url.strip():
            github.parse(repo_url, issue=False)
        if issue_url.strip():
            found = github.fetch_issue(issue_url)
            text, title, issue, repo_url, source = found["body"], found["title"], found["issue_url"], found["repo_url"], "github"
            meta = {k: found[k] for k in ("issue_number", "labels", "created_at", "updated_at")}
        elif upload:
            text, source = upload.decode("utf-8-sig"), "upload"
        if max(len(text.encode("utf-8")), len(upload)) > MAX_BYTES:
            raise HTTPException(413, "Report is larger than 200 KB.")
        return pipeline.run(text, source, repo_url.strip() or None, title=title, issue_url=issue, **meta)
    except InputEvaluationError as e:
        raise HTTPException(502, str(e)[:500])
    except ValueError as e:  # GitHubError, PreparationError, bad UTF-8, pydantic errors, id mismatches
        raise HTTPException(400, str(e)[:500])


@app.get("/")
def index(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.get("/samples/{name}")
def sample_file(name: str):
    """Sample reports for the paste tab. Names are a single path segment."""
    if not re.fullmatch(r"[A-Za-z0-9._-]+", name):
        raise HTTPException(404)
    path = (SAMPLES / name).resolve()
    if path.parent != SAMPLES.resolve() or path.suffix.lower() not in {".md", ".txt"} or not path.is_file():
        raise HTTPException(404)
    return PlainTextResponse(path.read_text(encoding="utf-8"))


@app.post("/evaluate")
def evaluate(request: Request, text: str = Form(""), issue_url: str = Form(""), repo_url: str = Form(""),
             file: Optional[UploadFile] = File(None)):
    output = _evaluate(text, file, issue_url, repo_url)
    link = output.record.issue_url if (output.record.issue_url or "").startswith("https://github.com/") else None
    return templates.TemplateResponse(request, "result.html", {"output": output, "issue_link": link})


@app.post("/api/evaluate")
def api_evaluate(text: str = Form(""), issue_url: str = Form(""), repo_url: str = Form(""),
                 file: Optional[UploadFile] = File(None)):
    return _evaluate(text, file, issue_url, repo_url)

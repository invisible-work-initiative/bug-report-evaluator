"""Maintainer-facing web interface (INT-6). Nothing is stored; report text is never logged (INT-9)."""
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException

from ..integration import github, pipeline
from ..integration.intake import InputEvaluationError
from ..integration.models import CRITERIA

MAX_BYTES = 200 * 1024        # one report
MAX_REQUEST = 256 * 1024      # whole request (Content-Length)

app = FastAPI(title="Bug report evaluator (Integration prototype)")
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


def short(text: Optional[str]) -> str:
    """Evidence excerpt for the table: at most 3 lines and about 200 characters."""
    text = text or ""
    cut = "".join(text.splitlines(True)[:3])[:200]
    return cut + ("..." if cut != text else "")


templates.env.filters["short"] = short
templates.env.globals["CRITERIA"] = CRITERIA


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

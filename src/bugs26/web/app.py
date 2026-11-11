"""Maintainer-facing web interface (INT-6). Nothing is stored; report text is never logged (INT-9)."""
import json
from pathlib import Path
from typing import Optional
from urllib.parse import quote

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates

from ..integration import github, pipeline
from ..integration.intake import PreparationError

MAX_BYTES = 200 * 1024        # one report
MAX_REQUEST = 256 * 1024      # whole request (Content-Length)
app = FastAPI(title="Bug report evaluator (Integration prototype)")
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


class InputError(Exception):
    def __init__(self, status: int, message: str):
        self.status, self.message = status, message


def _error(request: Request, status: int, message: str):
    """/evaluate shows an HTML error page; the API returns JSON."""
    if request.url.path == "/evaluate":
        return templates.TemplateResponse(request, "error.html", {"message": message}, status_code=status)
    return JSONResponse({"detail": message}, status_code=status)


@app.middleware("http")
async def limit_size(request: Request, call_next):
    """Reject oversized requests before the body is parsed."""
    length = request.headers.get("content-length", "")
    if length.isdigit() and int(length) > MAX_REQUEST:
        return _error(request, 413, "Request is larger than 256 KB.")
    return await call_next(request)


@app.exception_handler(InputError)
async def input_error(request: Request, exc: InputError):
    return _error(request, exc.status, exc.message)


def _evaluate(text: str, file: Optional[UploadFile], issue_url: str, repo_url: str):
    """Pick exactly one source (paste / upload / GitHub issue) and run the pipeline."""
    upload = b""
    if file is not None and file.filename:
        if not file.filename.lower().endswith((".md", ".txt")):
            raise InputError(400, "Only .md or .txt files are accepted.")
        upload = file.file.read(MAX_BYTES + 1)  # an empty upload is ignored
    sources = [bool(text.strip()), bool(upload), bool(issue_url.strip())]
    if sum(sources) != 1:
        raise InputError(400, "Provide exactly one of: pasted text, an uploaded file, or a GitHub issue URL.")
    title, issue = None, None
    try:
        if issue_url.strip():
            found = github.fetch_issue(issue_url)
            text, title, issue, repo_url, source = found["body"], found["title"], found["issue_url"], found["repo_url"], "github"
        elif upload:
            if len(upload) > MAX_BYTES:
                raise InputError(413, "File is larger than 200 KB.")
            try:
                text, source = upload.decode("utf-8-sig"), "upload"
            except UnicodeDecodeError:
                raise InputError(400, "File must be UTF-8 text.")
        else:
            source = "paste"
        if len(text.encode("utf-8")) > MAX_BYTES:
            raise InputError(413, "Report is larger than 200 KB.")
        return pipeline.run(text, source, repo_url.strip() or None, title=title, issue_url=issue)
    except (github.GitHubError, PreparationError) as e:
        raise InputError(400, str(e))


@app.get("/")
def index(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.post("/evaluate")
def evaluate(request: Request, text: str = Form(""), issue_url: str = Form(""), repo_url: str = Form(""),
                   file: Optional[UploadFile] = File(None)):
    output = _evaluate(text, file, issue_url, repo_url)
    subsystems = {"input_evaluation": "Input Evaluation", "claim_investigation": "Claim Investigation"}
    groups = [(label, [f for f in output.findings if f.source == key]) for key, label in subsystems.items()]
    json_uri = "data:application/json;charset=utf-8," + quote(json.dumps(output.model_dump(mode="json"), indent=2))
    return templates.TemplateResponse(request, "result.html", {
        "output": output, "groups": groups, "json_uri": json_uri,
        "lines": list(enumerate(output.original_body.splitlines(), 1))})


@app.post("/api/evaluate")
def api_evaluate(text: str = Form(""), issue_url: str = Form(""), repo_url: str = Form(""),
                       file: Optional[UploadFile] = File(None)):
    return _evaluate(text, file, issue_url, repo_url)

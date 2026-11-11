"""Maintainer-facing web interface (INT-6). Nothing is stored; report text is never logged (INT-9)."""
import json
from pathlib import Path
from typing import Optional
from urllib.parse import quote

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.templating import Jinja2Templates

from ..integration import pipeline

MAX_BYTES = 200 * 1024
app = FastAPI(title="Bug report evaluator (Integration prototype)")
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


async def _evaluate(text: str, file: Optional[UploadFile], repo_url: str):
    """Read the pasted text or uploaded file, run the pipeline."""
    source = "paste"
    if file is not None and file.filename:
        if not file.filename.lower().endswith((".md", ".txt")):
            raise HTTPException(400, "Only .md or .txt files are accepted.")
        data = await file.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            raise HTTPException(413, "File is larger than 200 KB.")
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            raise HTTPException(400, "File must be UTF-8 text.")
        source = "upload"
    if len(text.encode("utf-8")) > MAX_BYTES:
        raise HTTPException(413, "Report is larger than 200 KB.")
    if not text.strip():
        raise HTTPException(400, "Paste a report or upload a file.")
    return pipeline.run(text, source, repo_url.strip() or None)


@app.get("/")
def index(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.post("/evaluate")
async def evaluate(request: Request, text: str = Form(""), repo_url: str = Form(""),
                   file: Optional[UploadFile] = File(None)):
    output = await _evaluate(text, file, repo_url)
    subsystems = {"input_evaluation": "Input Evaluation", "claim_investigation": "Claim Investigation"}
    groups = [(label, [f for f in output.findings if f.source == key]) for key, label in subsystems.items()]
    json_uri = "data:application/json;charset=utf-8," + quote(json.dumps(output.model_dump(mode="json"), indent=2))
    return templates.TemplateResponse(request, "result.html",
                                      {"output": output, "groups": groups, "json_uri": json_uri})


@app.post("/api/evaluate")
async def api_evaluate(text: str = Form(""), repo_url: str = Form(""),
                       file: Optional[UploadFile] = File(None)):
    return await _evaluate(text, file, repo_url)

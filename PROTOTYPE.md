# Integration Subsystem Prototype (iteration 1)

A small, in-memory prototype of the **Integration** subsystem of the bug report evaluator. It takes a bug report (pasted or uploaded as `.md`/`.txt`), preserves and structures it, sends it through Input Evaluation and Claim Investigation, and returns the combined findings to the maintainer as an HTML page or JSON.

Input Evaluation (IE) and Claim Investigation (CI) belong to other teams. Here they are **placeholder stubs** behind small interfaces so the real code can be dropped in.

No database, no LLM, no network calls, no GitHub API. Nothing is written to disk or logged.

## Run

```
pip install -e .[dev]
uvicorn bugs26.web.app:app --reload
pytest
```

Open http://127.0.0.1:8000/ , paste a report or upload one from `samples/`, and press Evaluate. JSON is also available with
`curl -F "file=@samples/good-report.md" http://127.0.0.1:8000/api/evaluate`.

## Pipeline

```
paste / .md / .txt upload (+ optional repo URL)           web/app.py
  -> intake.receive()            INT-1   RawReport (verbatim text, sha256, report_id)
  -> intake.structure()          INT-2   StructuredReport (exact substrings; missing = None)
  -> InputEvaluator.evaluate()   INT-3   gets original + structured -> findings + investigation requests
  -> route.to_investigation()    INT-4   adds report context -> ClaimInvestigator.investigate()
  -> assemble.collect()          INT-5,7,8  findings from both, linked to report_id, evidence unchanged
  -> assemble.build_output()     INT-6   MaintainerOutput {summary, findings, could_not_check}
  -> HTML page / JSON            INT-6
```

Code: `src/bugs26/integration/` (`models`, `intake`, `route`, `assemble`, `pipeline`), `src/bugs26/stubs/`, `src/bugs26/web/`.
`pipeline.run(text, source, repo_url=None, evaluator=None, investigator=None)` takes any object that implements the `InputEvaluator` / `ClaimInvestigator` protocols.

## Traceability

| Req | Implemented in | Test |
|---|---|---|
| INT-1 receive reports | `intake.receive`, `web/app.py` | `tests/test_int_1.py`, `tests/test_web.py` |
| INT-2 preserve and structure | `intake.receive` (verbatim), `intake.structure` | `tests/test_int_2.py` |
| INT-3 send both versions to IE | `pipeline.run`, `InputEvaluator` protocol | `tests/test_int_3.py` |
| INT-4 requests + context to CI | `route.to_investigation`, `ClaimInvestigator` protocol | `tests/test_int_4.py` |
| INT-5 collect findings | `assemble.collect` | `tests/test_int_5.py` |
| INT-6 output to maintainer | `assemble.build_output`, `web/app.py`, templates | `tests/test_int_6.py`, `tests/test_web.py` |
| INT-7 reports linked to findings | `report_id` on every finding; `assemble.collect` rejects mismatches | `tests/test_int_7.py` |
| INT-8 evidence unchanged | findings passed through without copying fields | `tests/test_int_8.py` |
| INT-9 no reporter linking | no identity field in any model; no storage; no logging | `tests/test_int_9.py` |
| R4 state what was not checked | `assemble.build_output` (`could_not_check`, fixed note) | `tests/test_int_6.py` |

## Placeholders

- `stubs/input_evaluation_stub.py`: only checks that title, steps, expected, observed and environment sections exist. Each code reference becomes an investigation request.
- `stubs/claim_investigation_stub.py`: returns `could_not_check` for every request.
- Their findings are labelled `[PLACEHOLDER ...]` and the output always says Claim Investigation is not checking anything.
- `intake.structure` is regex-based (headings, `**Label:**`, `Label:` lines) and will miss unusual formats; missing parts are `None`, never guessed.
- Not done yet: fetching reports from GitHub (INT-1 "from supported GitHub repositories"), real IE/CI.
- JSON download on the result page is a `data:` link, so nothing is kept on the server.

# Integration Subsystem Prototype (iteration 2)

A small, in-memory prototype of the **Integration** subsystem of the bug report evaluator. It takes a bug report (pasted, uploaded as `.md`/`.txt`, or fetched from a public GitHub issue URL), preserves and structures it, runs Input Evaluation, routes to Claim Investigation when appropriate, and returns the combined findings to the maintainer as an HTML page or JSON.

Input Evaluation (IE) and Claim Investigation (CI) belong to other teams. Here they are **placeholder stubs** behind small interfaces so the real code can be dropped in.

No database, no LLM. The only network call is the optional GitHub issue fetch (stdlib `urllib`). Nothing is written to disk or logged.

## Run

```
pip install -e .[dev]
python -m bugs26.web          # http://127.0.0.1:8000/  (access log is off, INT-9)
pytest
```

Paste a report, upload one from `samples/`, or give a GitHub issue URL (exactly one source). JSON is also available:
`curl -F "file=@samples/good-report.md" http://127.0.0.1:8000/api/evaluate`.
Set `GITHUB_TOKEN` to raise GitHub's rate limit (optional).

## Pipeline

```
paste / .md,.txt upload / GitHub issue URL                 web/app.py (+ integration/github.py)
  -> intake.receive()            INT-1   RawReport: original_title + original_body verbatim, sha256, report_id
  -> intake.structure()          INT-2   StructuredReport: sections as exact spans of the body
  -> intake.verify_structured()  INT-2   every span must equal the original slice, else PreparationError (run stops)
  -> InputEvaluator.evaluate()   INT-3   gets original + structured -> decision, findings, investigation requests
  -> route.to_investigation()    INT-4   routing rule below; adds report context -> ClaimInvestigator.investigate()
  -> assemble.collect()          INT-5,7,8  findings from both, linked to report_id, evidence unchanged
  -> assemble.build_output()     INT-6   MaintainerOutput (decision, findings, could_not_check, original, structured)
  -> HTML page / JSON            INT-6
```

**Routing rule (BRE-DR.11):** Claim Investigation is called only if IE's decision is `investigate` AND IE sent at least one request. If the decision is `request_more_information` or `do_not_investigate`, CI is skipped and "Claims not investigated: <reason>" is shown under Could not check. If the decision is `investigate` but there are no requests, "No specific bug claim was identified" is shown.

**Structuring:** sections come from markdown headings and from a line that is only a bold label (`**Expected:**`, optionally followed by text). Bold counts only for known labels, nothing inside ``` or ~~~ fences counts, and labels match known aliases exactly or as a whole-word prefix (never as a substring). Repeated sections are all kept; unknown headings and preamble go to `unmapped`. Edges are trimmed by moving the span, never by changing text.

## Traceability

| Req | Implemented in | Test |
|---|---|---|
| INT-1 receive reports (paste, upload, GitHub) | `intake.receive`, `integration/github.py`, `web/app.py` | `tests/test_int_1.py`, `tests/test_web.py` |
| INT-2 preserve and structure | `intake.receive` (verbatim), `intake.structure`, `intake.verify_structured` | `tests/test_int_2.py` |
| INT-3 send both versions to IE | `pipeline.run`, `InputEvaluator` protocol | `tests/test_int_3.py` |
| INT-4 requests + context to CI, routing rule | `route.to_investigation`, `ClaimInvestigator` protocol | `tests/test_int_4.py` |
| INT-5 collect findings | `assemble.collect` | `tests/test_int_5.py` |
| INT-6 output to maintainer | `assemble.build_output`, `web/app.py`, templates | `tests/test_int_6.py`, `tests/test_web.py` |
| INT-7 reports linked to findings | `report_id` on findings and requests; `assemble.collect`/`route` reject mismatches | `tests/test_int_7.py`, `tests/test_int_4.py` |
| INT-8 evidence unchanged | findings passed through without copying fields | `tests/test_int_8.py` |
| INT-9 no reporter linking | no identity field in any model; GitHub `user` etc. dropped; no storage; no logging; access log off | `tests/test_int_9.py` |
| R4 state what was not checked | `assemble.build_output` (`could_not_check` = IE + CI limits + parse gaps) | `tests/test_int_6.py`, `tests/test_int_4.py` |

## Placeholders / not done

- `stubs/input_evaluation_stub.py`: only checks that description, steps, expected, observed and environment sections exist (C1-C5). C6 (evidence) and C7 (clarity) are always `unable_to_judge`. Decision is a simple rule on section presence and code references. Content quality is not judged.
- `stubs/claim_investigation_stub.py`: returns `could_not_check` for every request and says no code was examined.
- Their findings are labelled `[PLACEHOLDER ...]`.
- `intake.structure` is rule-based and will miss unusual formats; unmatched text stays visible under `unmapped`, missing parts are listed as "No ... section found", nothing is guessed.
- GitHub fetch handles one issue by URL only (no webhooks, no listing, no comments). The GitHub call runs inside the request and is not cached.
- JSON download on the result page is a `data:` link, so nothing is kept on the server.

# Integration Subsystem Prototype (iteration 5)

A small, in-memory prototype of the **Integration** subsystem of the bug report evaluator. It takes a bug report (pasted, uploaded as `.md`/`.txt`, or fetched from a public GitHub issue URL), preserves and structures it, runs Input Evaluation, routes to Claim Investigation when appropriate, and returns the combined findings to the maintainer as an HTML page or JSON.

Input Evaluation (IE) and Claim Investigation (CI) belong to other teams. Here they are **placeholder stubs** behind small interfaces so the real code can be dropped in.

No database, no LLM. The only network call is the optional GitHub issue fetch (stdlib `urllib`). Nothing is written to disk or logged.

## Run

Needs Python 3.10 or newer. From the repository root:

```
python -m venv .venv
.venv\Scripts\Activate.ps1          # Windows PowerShell
source .venv/bin/activate           # macOS / Linux
python -m pip install -e ".[dev]"
python -m pytest
python -m bugs26.web                # http://127.0.0.1:8000/  (access log is off, INT-9)
```

Paste a report, upload one from `samples/`, or give a GitHub issue URL (exactly one source). `samples/issue-form-report.md` is a synthetic issue-form style report that works offline and shows the "investigate" path with Claim Investigation rows. JSON is also available (on Windows use `curl.exe`, plain `curl` is a PowerShell alias):
`curl -F "file=@samples/good-report.md" http://127.0.0.1:8000/api/evaluate`.
The optional repository URL for pasted or uploaded reports must be `https://github.com/OWNER/REPO` and listed in `supported_repos.txt`.
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

**Structuring (`intake.structure`):** a section starts at a markdown heading or at a bold label line (`**Expected:** text`). Markers inside ``` / ~~~ fences (closing fence: same character, at least as long) and inside `<!-- ... -->` comments are ignored. A bold label followed by text counts only if it has a colon (`**Expected:** x` yes, `**Expected** it to open...` no); bold counts only for known labels. `## Expected: it should save` keeps the text after the colon as the section text. Labels match known aliases exactly, as a whole-word prefix, or (multi-word aliases, plus `version`/`versions` for environment) as a whole-word suffix, never as a mid-word substring. GitHub issue-form headings are covered (`What happened?` is observed, `What did you expect to happen?`, `How can we reproduce it`, `Reproducible Example`, `Installed Versions`, ...). Sections with no body are kept (label kept, empty span); a section holding only HTML comments counts as not written (`meaningful_text`). A report with no markers at all (freeform text) is mapped entirely to `description` (the section's label stays null; the field mapping does the work, spans untouched); if there are headings but none is recognised, could-not-check says so. `_No response_` (GitHub forms) counts as empty. Repeated sections are all kept; unknown headings and preamble go to `unmapped`. Lines split like `str.splitlines` (lone CR works). Edges are trimmed by moving the span, never by changing text. The title is only the GitHub issue title (`original_title`); pasted or uploaded reports have none.

**Evidence (R3):** a report excerpt carries its char span (`start`/`end`); the result page computes the line numbers from it and links them to the line in the original report view. Integration does not extract code references or versions: finding claims is Input Evaluation's job (the placeholder IE does it with a regex).

**Supported repositories (INT-1):** GitHub issues are accepted only from the repositories in `src/bugs26/integration/supported_repos.txt` (one `owner/repo` per line, `#` comments, case-insensitive). Add a line and restart to support another.

**Failures:** if Claim Investigation raises, the failure goes to could-not-check ("Claim Investigation failed: ...") and the run continues. If Input Evaluation raises, the maintainer gets an error page (HTTP 502), never a fake result.

## Plugging in your subsystem

1. Implement `InputEvaluator` or `ClaimInvestigator` from `src/bugs26/integration/interfaces.py` (one method each).
2. Return the models from `integration/models.py`; set `report_id` on every finding and request; cite evidence; fill `not_checked`.
3. Try it: `pipeline.run(text, "paste", evaluator=MyIE(), investigator=MyCI())`.
4. Make it the default by changing the two defaults in `integration/pipeline.py`.
5. Run `pytest`. The interface agreements in `documentation/interfaces/` list the tests to re-run against your code.

**Could not check (R4):** IE limits + CI limits + one line `Sections not mapped: a, b, c` (the GitHub issue-form boilerplate headings are listed on purpose; INT-2 honesty). Missing sections are reported by the IE findings, not repeated here.

**Finding subject:** human-readable: the criterion name for IE findings, the claim text for CI findings. A CI finding cites a `report_excerpt` at the claim's span, so it links to its line.

## Glossary of design IDs

The IDs below come from the team's SYSEN 5100 design compendium (HW7), which is not in this repository.

| ID | Meaning |
|---|---|
| IF02 | Integration to IE: the prepared report (fields in a consistent structure, original text, source links). |
| IF03 | Integration to IE: preparation issues (missing fields, problems). No guessed content. |
| IF04 | IE to Integration: quality assessment, sufficiency, missing information, limits. |
| IF05 | IE to Integration: checkable claims, each with its location in the original report. |
| IF06 | Integration to CI: report, claims, evaluation context, source links. Only when there is enough information. |
| IF07 | CI to Integration: a finding per claim, with evidence and source links. |
| IF08 | CI to Integration: limits or failures, with reasons. Findings for other claims are kept. |
| IF11 | Design input from IE: required report fields and sufficiency rules. |
| IF12 | Design input from CI: claim and evidence fields. |
| BRE-DR.11 | Routing rule: send to CI only when the report is sufficient AND there is at least one claim. |

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

- `stubs/input_evaluation_stub.py`: only checks that description, steps, expected, observed and environment sections exist (C1-C5). C6 (evidence) and C7 (clarity) are always `unable_to_judge`. Decision is a simple rule on section presence and code references. Content quality is not judged. It also finds the code references (claims) by regex.
- `stubs/claim_investigation_stub.py`: returns `could_not_check` for every request and says no code was examined.
- Their findings are labelled `[PLACEHOLDER ...]`.
- `intake.structure` is rule-based and will miss unusual formats; unmatched text stays visible under `unmapped`, missing parts are listed as "No ... section found", nothing is guessed.
- GitHub fetch handles one issue by URL only (no webhooks, no listing, no comments). The GitHub call runs in the server's threadpool (endpoints are plain `def`) and is not cached. Owner/repo must be ASCII, `.`/`..` are refused.
- JSON download on the result page is a `data:` link, so nothing is kept on the server.

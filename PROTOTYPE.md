# Integration Subsystem Prototype (iteration 6)

A small, in-memory prototype of the **Integration** subsystem of the bug report evaluator. It takes a bug report (pasted, uploaded as `.md`/`.txt`, or fetched from a public GitHub issue URL), preserves and structures it, runs Input Evaluation, sends each identified claim to Claim Investigation, and returns the combined results to the maintainer as an HTML page or JSON.

Input Evaluation (IE) and Claim Investigation (CI) belong to other teams. Here they are **placeholder stubs** behind small interfaces so the real code can be dropped in. Their data formats are the other teams' drafts, not ours: the `IE...` classes in `integration/models.py` follow the IE draft v1, the `CI...` classes follow the CI draft 0.2 (provisional). Integration's own classes are `RawReport`, `StructuredReport`, `CIRequest` (proposed) and `MaintainerOutput`.

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

Paste a report, upload one from `samples/`, or give a GitHub issue URL (exactly one source). `samples/issue-form-report.md` is a synthetic issue-form style report that works offline and shows the claims table with Claim Investigation rows. JSON is also available (on Windows use `curl.exe`, plain `curl` is a PowerShell alias):
`curl -F "file=@samples/good-report.md" http://127.0.0.1:8000/api/evaluate`.
The optional repository URL for pasted or uploaded reports must be `https://github.com/OWNER/REPO` and listed in `supported_repos.txt`.
Set `GITHUB_TOKEN` to raise GitHub's rate limit (optional).

**Supported repositories (INT-1, admin note):** GitHub issues are accepted only from the repositories in `src/bugs26/integration/supported_repos.txt` (one `owner/repo` per line, `#` comments, case-insensitive). The maintainer sees "This repository is not supported yet". To support another, add a line and restart the server.

## Pipeline

```
paste / .md,.txt upload / GitHub issue URL                 web/app.py (+ integration/github.py)
  -> intake.receive()            INT-1   RawReport: title + raw_body verbatim, report_id/request_id/snapshot_id, GitHub metadata
  -> intake.structure()          INT-2   StructuredReport: IE-style sections (exact slices of raw_body, 1-based source_lines)
  -> intake.verify_structured()  INT-2   every value, line range and label must check out, else PreparationError (run stops)
  -> InputEvaluator.evaluate()   INT-3   one IEReportRecord (raw_body + sections) -> IEResult
  -> route.match_ie()            INT-5   request_id + snapshot_id must match, C1-C7 once each, else InputEvaluationError (502)
  -> route.to_investigation()    INT-4   one CIRequest per identified claim -> ClaimInvestigator.investigate() -> CIResult
  -> assemble.build_output()     INT-5..8  MaintainerOutput: IEResult and CIResults passed through unchanged, could_not_check
  -> HTML page / JSON            INT-6
```

**Routing (mechanical, per the IE draft):** one CI call per entry in `identified_claims`. CI is skipped, and the reason is shown under Could not check, when IE's `processing_status` is `invalid_input` or `failed`, `claim_extraction.status` is `not_performed`, or `no_checkable_claims` is true. IE's draft has no decision field, so there is none. A CI answer for another claim or request, or with zero or several findings for the claim, is a failure for that claim and is listed under Could not check.

**Structuring (`intake.structure`):** a section starts at a markdown heading or a bold label line (`**Expected:** text`). Markers inside ``` / ~~~ fences (closing fence: same character, at least as long) and inside `<!-- ... -->` comments are ignored. A bold label followed by text counts only if it has a colon, and bold counts only for known labels. `## Expected: it should save` keeps the text after the colon as the value. Headings are matched to the six IE concepts (`bug_description`, `steps_to_reproduce`, `expected_behavior`, `observed_behavior`, `environment_version`, `supporting_evidence`) by known aliases: exactly, as a whole-word prefix, or (multi-word aliases, plus `version`/`versions`) as a whole-word suffix, never as a mid-word substring. Any other heading is kept as a section with `recognition: "unrecognized"` and `semantic_concept: null`.
- `value` is the exact text under the heading, without the heading line. `provided` values have edge whitespace cut off (by moving the span); `blank` values keep the exact whitespace. `_No response_` and HTML comments are copied as they are; IE decides if they are useful.
- A report with no headings is free-form: `sections: []`, `extraction.mode: "free_form"`. Nothing is made up. Text before the first heading is not a section; it stays in `raw_body`.
- `source_lines` are 1-based, split on LF (a CRLF is one break). Integration's own notes (`preamble_not_a_section`, `unrecognized_headings`, `no_headings_recognised`) go to `extraction.diagnostics`. They are not maintainer gaps: IE reads the raw text.
- No issue template is known, so `field_id`, `required` and `template_id` are `null`, and `absent` is never sent. `body_source` is always `current` (the initial text is not available).
- Pasted and uploaded reports have no issue number, URL or timestamps; those stay `null` and are never made up ("pending IE Q3": the IE draft requires them). The title is the GitHub issue title, `""` otherwise.

**Evidence (R3):** IE evidence carries `source`, `section_id` and 1-based `lines`; the result page links the lines into the original report view. CI evidence carries `type`, `reference` and `explanation`. Integration does not extract code references or versions: finding claims is IE's job (the placeholder IE does it with a regex).

**Failures:** if Claim Investigation raises, the failure goes to could-not-check and the run continues. If Input Evaluation raises, or its answer does not match the request, the maintainer gets an error page (HTTP 502), never a fake result. `invalid_input`, `failed` and `partial` results are shown as a failure or with their limits, never as a complete evaluation.

**Transport:** in-process Python calls, provisional pending the IE transport decision (2026-11-24). No timeout is defined.

## Plugging in your subsystem

1. Implement `InputEvaluator` or `ClaimInvestigator` from `src/bugs26/integration/interfaces.py` (one method each).
2. Take and return the models from `integration/models.py` (the `IE...` or `CI...` classes; unknown fields are rejected).
3. Try it: `pipeline.run(text, "paste", evaluator=MyIE(), investigator=MyCI())`.
4. Make it the default by changing the two defaults in `integration/pipeline.py`.
5. Run `pytest`. The interface agreements in `documentation/interfaces/` list the tests to re-run against your code.

**Could not check (R4):** IE `unevaluated_criteria` with reasons, `U` ratings, a non-`completed` processing status, an incomplete claim extraction with its reason, IE error diagnostics, CI `insufficient evidence` and limitations, and Integration-level failures (skipped or failed CI calls). The maintainer page shows them in one list.

## Glossary of design IDs

The IDs below come from the team's SYSEN 5100 design compendium (HW7), which is not in this repository.

| ID | Meaning |
|---|---|
| IF02 | Integration to IE: the prepared report (fields in a consistent structure, original text, source links). |
| IF03 | Integration to IE: preparation issues (missing fields, problems). No guessed content. |
| IF04 | IE to Integration: quality assessment, sufficiency, missing information, limits. |
| IF05 | IE to Integration: checkable claims, each with its location in the original report. |
| IF06 | Integration to CI: report, claims, evaluation context, source links. |
| IF07 | CI to Integration: a finding per claim, with evidence and source links. |
| IF08 | CI to Integration: limits or failures, with reasons. Findings for other claims are kept. |
| IF11 | Design input from IE: required report fields and sufficiency rules. |
| IF12 | Design input from CI: claim and evidence fields. |
| BRE-DR.11 | Old routing rule (send to CI only when the report is sufficient AND there is a claim). Replaced by the mechanical rule above; the IE draft has no decision field. |

## Traceability

| Req | Implemented in | Test |
|---|---|---|
| INT-1 receive reports (paste, upload, GitHub) | `intake.receive`, `integration/github.py`, `web/app.py` | `tests/test_int_1.py`, `tests/test_web.py` |
| INT-2 preserve and structure | `intake.receive` (verbatim), `intake.structure`, `intake.verify_structured` | `tests/test_int_2.py` |
| INT-3 send both versions to IE | `pipeline.run`, `intake.to_record`, `InputEvaluator` protocol | `tests/test_int_3.py` |
| INT-4 requests + context to CI | `route.to_investigation`, `ClaimInvestigator` protocol | `tests/test_int_4.py` |
| INT-5 collect findings | `route.match_ie`, `assemble.build_output` | `tests/test_int_5.py` |
| INT-6 output to maintainer | `assemble.build_output`, `web/app.py`, templates | `tests/test_int_6.py`, `tests/test_web.py` |
| INT-7 reports linked to findings | `request_id`/`snapshot_id` matching, `claim_id` on CI results; `route`/`assemble` reject mismatches | `tests/test_int_7.py`, `tests/test_int_4.py` |
| INT-8 evidence unchanged | `IEResult` and `CIResult` objects are placed in the output as received | `tests/test_int_8.py` |
| INT-9 no reporter linking | no identity field in any model; GitHub `user` etc. dropped; no storage; no logging; access log off | `tests/test_int_9.py` |
| R4 state what was not checked | `assemble.could_not_check` | `tests/test_int_6.py`, `tests/test_int_4.py` |

## Placeholders / not done

- `stubs/input_evaluation_stub.py`: rates C1-C5 `P` (a section with content exists, with a quotation) or `M` (none, with an absence check); C6 and C7 are always unevaluated (`dependency_unavailable`), so the status is `partial`. For a free-form report C1-C5 are unevaluated (`unsupported_content`). Content quality is not judged. It finds the claims by regex, and pins the criteria version `git:b1820e5:documentation/bug-report-quality-criteria.md`. Its findings are labelled `[PLACEHOLDER ...]`.
- `stubs/claim_investigation_stub.py`: returns `insufficient evidence` for every claim, with the limitation "no code was examined".
- `intake.structure` is rule-based and will miss unusual formats; unmatched headings stay visible as `unrecognized` sections, nothing is guessed.
- GitHub fetch handles one issue by URL only (no webhooks, no listing, no comments). The GitHub call runs in the server's threadpool (endpoints are plain `def`) and is not cached. Owner/repo must be ASCII, `.`/`..` are refused.
- JSON download on the result page is a `data:` link, so nothing is kept on the server.
- Open questions to the IE and CI teams are in the two files under `documentation/interfaces/`.

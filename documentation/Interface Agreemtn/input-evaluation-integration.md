# Interface agreement: Input Evaluation and Integration

**Interface name:** Input Evaluation–Integration report evaluation interface  
**Owners:** Julian Jiang (`Yulinjiang599`), Input Evaluation; TBD, Integration (see Open item 1)  
**Status:** draft  
**Version and date approved:** Not yet approved. Proposed as version 1 for Gate 2.

## 1. Purpose and scope

Integration gives Input Evaluation (IE) each incoming bug report. IE returns a quality finding for every criterion and the checkable claims that Integration then sends to Claim Investigation.

This agreement covers:

- the report record Integration sends to IE (Section 4.1);
- the evaluation result IE sends back to Integration (Section 4.2);
- the rules both sides follow for identifiers, versions, and errors (Section 4.3).

It does not cover:

- how Integration retrieves reports from GitHub, or how IE evaluates them (models, prompts, code);
- how Integration forwards claims to Claim Investigation, which belongs in the Integration–Claim Investigation agreement;
- whether a claim is true, which Claim Investigation decides.

Three rules set the boundary:

1. Integration passes on the reporter's words exactly. It does not fill in missing information, rewrite unclear text, or judge quality.
2. IE judges report quality and identifies claims. It never marks a claim as verified. A low-quality report can still contain checkable claims.
3. Only the initial issue submission is evaluated, as the quality criteria require. Comments and later edits are out of scope.

## 2. Related documents

- [System requirements](../system-requirements.md), R1–R6 (main). The team's expanded R1–R9 draft is in the [System Requirements Google Doc](https://docs.google.com/document/d/16a4n3GOQUCMJNqrWSI4KCzBsWQk-W8XhA2J3N4qtpGE/edit) and is not yet merged.
- [Input Evaluation requirements IE1–IE11](https://github.com/invisible-work-initiative/bug-report-evaluator/blob/Input-evaluation/documentation/System%20Requirement/input_system-requirements_final_Version.md) (draft, `Input-evaluation` branch).
- [Integration requirements INT-1–INT-9](https://github.com/invisible-work-initiative/bug-report-evaluator/pull/13) (draft, PR #13).
- [Quality criteria C1–C7 and the P/M/N/A/U scale](https://github.com/invisible-work-initiative/bug-report-evaluator/blob/b1820e55e2f5e3a03a8888fad1a4805b3356832b/documentation/bug-report-quality-criteria.md), pinned at commit `b1820e5`. Use its Final Criteria Decisions where they revise earlier guidance.
- [Gate 1 draft of this interface](https://github.com/invisible-work-initiative/bug-report-evaluator/blob/Input-evaluation/documentation/Interface%20Agreemtn/evaluation-integration-interface%20agreement.md) (Integration → IE only).
- [Interface management process](../interface-agreements.md).
- Outside standards: JSON ([RFC 8259](https://www.rfc-editor.org/rfc/rfc8259)), timestamps ([RFC 3339](https://www.rfc-editor.org/rfc/rfc3339)), JSON Pointer ([RFC 6901](https://www.rfc-editor.org/rfc/rfc6901)).

## 3. Interface description

```text
                 report record (4.1)
 Integration  ─────────────────────────>  Input Evaluation
              <─────────────────────────
                evaluation result (4.2)
      │
      └── forwards claims + report context to Claim Investigation
          (separate Integration–Claim Investigation agreement)
```

| Interaction type | Applies? |
|---|---|
| Information | Yes. One JSON record each way per report. |
| Physical, Energy, Material | Not applicable. |
| Human | Not applicable. No person acts at the boundary during an exchange. |

## 4. Items that cross the interface

### 4.1 Report record (Integration → IE)

**Direction:** Integration → Input Evaluation.  
**Description:** One bug report: the original title and body, where it came from, and any sections Integration could extract. IE evaluates it against C1–C7 and looks for checkable claims.  
**Characteristics:** One UTF-8 JSON object per evaluation attempt, with the fields below. All fields are required; fields marked "or null" must be present with `null` when unknown.

| Field | Type and allowed values | Meaning |
|---|---|---|
| `schema_version` | `"1.0"` | Version of this agreement's record format |
| `request_id` | non-empty string | Integration's ID for this evaluation attempt |
| `snapshot_id` | non-empty string | Integration's ID for this exact copy of the report text |
| `repository` | `"owner/project"` | Source repository |
| `issue_number` | positive integer | Issue number in that repository |
| `issue_url` | `https://github.com/<owner>/<project>/issues/<n>` | Must match `repository` and `issue_number` |
| `title` | string, `""` allowed | Exact title |
| `raw_body` | string, `""` allowed | Exact, complete Markdown body. Never shortened or generated. A body GitHub returns as null is sent as `""`. |
| `body_source` | `"initial"` or `"current"` | `initial`: the text as first submitted. `current`: the latest text, sent only when the initial text could not be retrieved. |
| `labels` | array of strings, `[]` allowed | Labels on the issue |
| `created_at` | RFC 3339 timestamp | When the issue was created |
| `updated_at` | RFC 3339 timestamp, not earlier than `created_at` | When the issue was last updated |
| `sections` | array of Section objects, `[]` allowed | Sections Integration could extract reliably |
| `extraction` | Extraction object | How the sections were extracted |

**Section object**

| Field | Type and allowed values | Meaning |
|---|---|---|
| `section_id` | non-empty string, unique in the record | Reference used by IE's evidence |
| `field_id` | string or null | Issue Form field ID, only when the template provides one |
| `original_label` | non-empty string | Exact heading or field label |
| `required` | boolean or null | Whether the template marks the field required, when known |
| `status` | `provided`, `blank`, or `absent` | See the rules below |
| `value` | string or null | Exact text under the heading, without the heading line |
| `recognition` | `recognized` or `unrecognized` | Whether Integration matched it to a known template field or concept |
| `semantic_concept` | one of the six concepts below, or null | Optional label for what the section contains |
| `source_lines` | `{"start": n, "end": n}` or null | Lines of `raw_body` covering the heading and its value |

Section rules:

- **provided:** the field has non-blank text. `value` is copied exactly, including template text such as "No response". IE, not Integration, decides whether that text is useful.
- **blank:** the heading is present but its text is empty or whitespace. `value` keeps the exact string.
- **absent:** a field defined by a known template (`extraction.template_id` is not null) does not appear. `value` and `source_lines` are null. Absent sections are never invented for headings Integration cannot identify.
- An unknown heading is kept as a section with `recognition: "unrecognized"` and `semantic_concept: null`. It is still valid input.
- `field_id` and `required` stay null unless the template that applied when the issue was submitted is known.
- `value` must appear exactly inside the `source_lines` it points to. Repeated headings become separate sections. Integration does not merge or rewrite sections.
- A blank or absent required field is a quality problem for IE to judge, not an invalid record.

**Extraction object**

| Field | Type and allowed values |
|---|---|
| `mode` | `structured`, `free_form`, `unsupported_template`, or `parse_error` |
| `template_id` | string or null, for example `path@commit` of the issue template |
| `diagnostics` | array of `{"code": string, "message": string}`; must be non-empty for `unsupported_template` and `parse_error` |

- A free-form report with `sections: []` is valid. IE evaluates the title and body directly. A missing heading does not mean the information is missing.
- For `unsupported_template` or `parse_error`, Integration still sends the complete body and only the sections it trusts. IE evaluates the raw text and adds the warning `input_degraded`.
- `semantic_concept` is optional. Allowed values: `bug_description`, `steps_to_reproduce`, `expected_behavior`, `observed_behavior`, `environment_version`, `supporting_evidence`. When Integration is unsure, it sends `null`. A non-null concept requires `recognition: "recognized"`. IE may disagree with a concept and never needs one to evaluate a report.

**Proposed answers to the six Gate 1 questions** (Integration to confirm, Open item 2)

| Gate 1 question | Proposed answer |
|---|---|
| Can Integration provide both raw Markdown and sections? | Yes. `raw_body` is always sent and is the authoritative text; `sections` may be `[]`. |
| Which metadata is available? | Repository, issue number and URL, title, labels, created and updated times, plus `request_id`, `snapshot_id`, and `body_source`. |
| How are blank, absent, and unrecognized fields encoded? | `status` (`provided`, `blank`, `absent`) and `recognition` (`recognized`, `unrecognized`) are separate fields. |
| Are Issue Form field IDs and required status preserved? | Yes when the template is known; otherwise `null`. |
| Is semantic mapping included? | Optional, from a fixed list of six concepts; IE never depends on it. |
| How are parse errors and unsupported templates handled? | `extraction.mode` with diagnostics; IE falls back to the raw text and warns `input_degraded`. |

### 4.2 Evaluation result (IE → Integration)

**Direction:** Input Evaluation → Integration.  
**Description:** One result per report record: a finding for each criterion C1–C7 with its evidence, what IE could not evaluate and why, the checkable claims found, and the versions used. Integration includes the findings in the maintainer output and forwards the claims to Claim Investigation.  
**Characteristics:** One UTF-8 JSON object per evaluation attempt, including rejected and failed attempts. All fields are required.

| Field | Type and allowed values |
|---|---|
| `schema_version` | `"1.0"` |
| `request_id` | copied from the input, or null if it could not be read |
| `snapshot_id` | copied from the input, or null if it could not be read |
| `processing_status` | `completed`, `partial`, `invalid_input`, or `failed` |
| `criterion_findings` | array of Finding objects |
| `unevaluated_criteria` | array of criterion IDs whose finding is `unevaluated`; `[]` means every criterion was concluded |
| `claim_extraction` | `{"status": "completed" \| "partial" \| "not_performed", "reason": string or null}`; `reason` is null only when `completed` |
| `identified_claims` | array of Claim objects |
| `no_checkable_claims` | `true` if extraction completed and found no claims; `false` if claims were found; `null` if extraction did not complete |
| `diagnostics` | array of Diagnostic objects |
| `provenance` | Provenance object |

**Processing status**

| Status | When | What the result contains |
|---|---|---|
| `completed` | Valid input; everything finished | 7 concluded findings; `unevaluated_criteria: []`; claim extraction `completed`; no `error` diagnostics |
| `partial` | Valid input; some part could not be done | 7 findings, at least one `unevaluated` or claim extraction not completed; an `error` diagnostic for each part not done |
| `invalid_input` | The record breaks Section 4.1 or 4.3 | No findings or claims; extraction `not_performed`; at least one `error` diagnostic pointing to the bad field |
| `failed` | Valid input, but IE produced no usable result (for example, the criteria could not be loaded) | No findings or claims; at least one `error` diagnostic |

IE never reports an `invalid_input` or `failed` attempt as a completed evaluation.

**Finding object**

| Field | Type and allowed values |
|---|---|
| `criterion_id` | `C1` … `C7`, each exactly once |
| `criteria_version` | exact criteria revision used; equal to `provenance.criteria_version` |
| `evaluation_status` | `concluded` or `unevaluated` |
| `rating` | `P`, `M`, `N/A`, or `U` when concluded; `null` when unevaluated |
| `explanation` | non-empty sentence stating the finding |
| `evidence` | non-empty array of Evidence objects |
| `unevaluated_reason` | null when concluded; `{"code": string, "message": string}` when unevaluated |

How ratings map to outcomes:

- **P, M, N/A, and U are all concluded findings.** They describe the report. U means the report is contradictory, or its supplied evidence is inaccessible or unrelated, as the C6 rubric defines.
- **Unevaluated** means IE could not apply the rubric because of its own limitation: a service it needs failed, or the content is in a form or language it cannot process. Reason codes: `unsupported_content`, `unsupported_language`, `dependency_unavailable`, `internal_error`.
- Missing information that IE can identify is **M**, not unevaluated. An IE failure is never reported as M or U.
- N/A needs an explanation of why the criterion does not apply. Absence alone is not N/A.

**Evidence object**

| Field | Type and allowed values |
|---|---|
| `basis` | `quotation`, `absence_check`, or `source_reference` |
| `source` | `title`, `raw_body`, or `whole_report` (title and body together) |
| `section_id` | an input `section_id`, or null |
| `lines` | `{"start": n, "end": n}` within `raw_body`, or null for the whole source |
| `quote` | exact text from the source for `quotation`; null otherwise |
| `explanation` | non-empty: why this supports the finding, what was searched for, or what could not be accessed |

- `quotation`: `quote` appears exactly in the source, inside `lines` and inside the section when these are given.
- `absence_check`: supports an M finding. The explanation says what information was looked for and where.
- `source_reference`: points to content without quoting it, for example a link that turned out to be inaccessible.
- Lines are numbered from 1 by splitting `raw_body` on line feeds; `\r\n` counts as one break. Title and `whole_report` evidence use `lines: null`.

**Claim object**

| Field | Type and allowed values |
|---|---|
| `claim_id` | non-empty string, unique within the response; the full key is (`request_id`, `claim_id`) |
| `claim_text` | exact text of the claim from the title or body |
| `source` | a `quotation` Evidence object whose `quote` equals `claim_text` |
| `named_project_versions` | versions the report itself states for this claim, in order of first appearance; `[]` if none. Never inferred from dates or releases. |
| `relevant_context` | exact excerpt from the title or body that contains the claim and the surrounding information Claim Investigation needs |

A claim is a statement to be checked, not a verified fact. Integration keeps the snapshot (Section 4.3), so it can attach the full title and body when it forwards a claim.

**Provenance object**

| Field | Type and allowed values |
|---|---|
| `criteria_version` | exact criteria revision, for example `git:<commit>:<path>`; null if the criteria were never loaded |
| `evaluator_version` | IE implementation revision |
| `external_models` | array of `{"provider", "model", "version"}` for every external model actually used; `[]` if none |
| `evaluated_at` | RFC 3339 time the result was produced |

If a model provider exposes only a moving alias (such as "latest"), IE records the alias and adds the warning `model_version_unresolved`.

**Diagnostic object**

| Field | Type and allowed values |
|---|---|
| `severity` | `warning` or `error` |
| `code` | see below |
| `path` | JSON Pointer to the input field concerned (for example `/raw_body`), or null |
| `message` | non-empty explanation |

- Contract errors: `invalid_json`, `missing_required_field`, `invalid_type`, `invalid_value`, `unknown_field`, `unsupported_schema_version`, `source_mismatch`, `correlation_conflict`.
- Processing errors: the four unevaluated reason codes above.
- Warnings: `input_degraded`, `not_initial_submission`, `model_version_unresolved`.
- A `completed` result may contain warnings but never errors.

### 4.3 Shared rules

- **Format.** Each record is one UTF-8 JSON object. Required fields are always present. Unknown values are `null`, never strings such as `"unknown"` or `"N/A"`. (The rating `"N/A"` is a finding, not a missing value.)
- **Strict version.** `schema_version` must be `"1.0"`. Unknown fields and duplicate keys are rejected as `invalid_input`. Adding or changing a field needs a new version of this agreement.
- **Request ID.** Integration assigns a new `request_id` to each evaluation attempt. A resend after a timeout reuses the same ID and the same payload. A deliberate re-evaluation uses a new ID. The same ID with different content is a `correlation_conflict`.
- **Snapshot ID.** A `snapshot_id` names one fixed copy of the report text. New text gets a new snapshot ID. Integration keeps each snapshot so that evidence line numbers can be resolved later.
- **Initial submission.** Integration sends `body_source: "initial"` when it captured the issue when it was created or recovered the original text. Otherwise it sends `"current"`, and IE evaluates the text and adds the warning `not_initial_submission`. The maintainer output can then say that later edits may be included.
- **Matching results.** Integration matches each result to its request by `request_id` and `snapshot_id`. The first valid result for a request is final. A missing or invalid result is reported as a failure, never as success. If the input cannot be parsed as JSON, IE returns `invalid_input` with null IDs, and Integration matches the result through the transport call itself.
- **Forwarding.** Integration forwards every finding, unevaluated criterion, and claim it receives without dropping or changing them.
- **Privacy.** No reporter identity field crosses this interface, and neither side builds records that link one reporter across reports.
- **Transport.** The transport (function call, files, or HTTP) and its timeout are not decided yet (Open item 3). The transport does not change the record contents above.

## 5. Responsibilities

**Integration provides:** the original title and body exactly as submitted, source metadata, extracted sections with their presence states, template metadata when known, and a `request_id` and `snapshot_id` for each attempt.  
**Integration expects:** one result per request in the Section 4.2 format, with a finding and evidence for every criterion C1–C7, an explicit list of what could not be evaluated, the identified claims, and the versions used.  
**Input Evaluation provides:** contract validation, criterion findings with evidence, unevaluated criteria with reasons, identified claims with their source and context, provenance, and an explicit `invalid_input` or `failed` result when it cannot evaluate.  
**Input Evaluation expects:** records that follow Section 4.1, the reporter's unchanged wording, template metadata only when it is reliable, and no quality judgments added by Integration.

## 6. Interface requirements

| ID | Requirement | Traces to |
|---|---|---|
| IF-1 | Integration shall provide one report record per evaluation attempt to Input Evaluation with the fields and characteristics defined in Section 4.1. | R1; INT-3 |
| IF-2 | Integration shall provide the report title and body exactly as submitted and shall not add, rewrite, or infer report content. | R1, R3; INT-2 |
| IF-3 | Integration shall represent extracted sections, their presence states, and template metadata as defined in Section 4.1, and shall use only the allowed semantic concepts. | R1; INT-2 |
| IF-4 | Input Evaluation shall accept free-form and degraded-extraction records and evaluate them from the original title and body. | R1; IE1 |
| IF-5 | Input Evaluation shall validate each report record against Sections 4.1 and 4.3 and shall return `invalid_input` with diagnostics, not a normal evaluation, for any record that breaks them. | R4; IE8 |
| IF-6 | For each completed or partial evaluation, Input Evaluation shall provide exactly one finding per criterion C1–C7, each citing evidence as defined in Section 4.2. | R1, R3; IE1, IE2, IE6 |
| IF-7 | Input Evaluation shall identify each criterion it could not evaluate, with a reason, and shall return an empty list when every criterion was concluded. | R4; IE3 |
| IF-8 | Input Evaluation shall provide each identified claim with a unique ID, exact text, source location, named versions, and relevant context, or an explicit no-claims result. | R1, R3; IE5, IE7 |
| IF-9 | Input Evaluation shall record the criteria version, evaluator version, external models, and evaluation time in every result. | IE11 (draft system requirement R9.3) |
| IF-10 | Integration shall forward every finding, unevaluated criterion, and claim it receives from Input Evaluation without dropping or changing them. | R2, R3; INT-5, INT-7, INT-8 |
| IF-11 | Integration and Input Evaluation shall match results to requests by `request_id` and `snapshot_id`, and shall report a missing, invalid, or conflicting result as a failure. | R2, R4 |
| IF-12 | Neither subsystem shall pass reporter identity through this interface or create records that link one reporter across reports. | R6; IE9, INT-9 |

R1–R6 are the system requirements on main. IE and INT numbers refer to the draft subsystem requirements in Section 2.

## 7. Verification

The tests use the examples in Appendix A as starting fixtures. Results are recorded in the pull request that runs them, with the commit, fixture, expected and actual result, and who ran it.

| Requirement ID | Method | How | Performed by | Results |
|---|---|---|---|---|
| IF-1, IF-2 | Test | Run Integration on real issues and on A.1 and A.2. Compare title, body, and metadata with the GitHub source character by character. | Integration; IE checks | Not yet run |
| IF-3 | Test | Fixtures with provided, blank, absent, unrecognized, and repeated sections. Check the encodings and that every `value` is found in its `source_lines`. | Integration; IE checks | Not yet run |
| IF-4 | Test | A.2, an unsupported template, and a parse error with a valid body. IE returns seven findings and `input_degraded` where expected. | IE | Not yet run |
| IF-5 | Test | One record per contract violation: missing field, wrong type, bad version, malformed JSON, unknown field, section text not in body. Expect `invalid_input` with the right path and no findings (A.3, A.4). | IE; Integration checks it is shown as a failure | Not yet run |
| IF-6 | Test; Inspection | Check that every result has C1–C7 once and every quotation is found in the source. Both owners inspect a sample of findings to confirm the evidence supports them. | IE; Integration inspects | Not yet run |
| IF-7 | Test | Reports with missing information (expect M), contradictory information (expect U), an evidence service failure (expect unevaluated, A.7), and a complete control report (expect `[]`). | IE | Not yet run |
| IF-8 | Test | Reports with several claims, one named version, two compared versions, no claims (A.6), and interrupted extraction. | IE; Integration checks forwarding | Not yet run |
| IF-9 | Inspection | Check provenance in every test result, including a run with no model and a model exposed only as an alias. | IE | Not yet run |
| IF-10 | Test | Send results A.5, A.6, and a partial result through Integration and compare what it forwards with what it received. | Integration | Not yet run |
| IF-11 | Test | Resend after timeout with the same ID, re-evaluate with a new ID, reuse an ID with changed content, and return a malformed result. | Integration; IE | Not yet run |
| IF-12 | Inspection | Process several reports from the same reporter and inspect both sides' records and logs for identity links. | Both | Not yet run |
| All | Demonstration | Once the transport is chosen, run one report end to end from GitHub through IE and back to Integration. | Both | Not yet run |

These tests show that the interface works. They do not measure evaluation quality or claim recall, which are verified under IE4 and the system's historical evaluation.

## 8. Open items

Target dates are proposals until the responsible people confirm them.

| # | Item | Responsible | Target date |
|---|---|---|---|
| 1 | Name the Integration owner of this agreement. | Integration (Andy or Meshaal) | 2026-11-17 |
| 2 | Confirm the proposed answers to the six Gate 1 questions (Section 4.1), including whether Integration can provide the initial body text (`body_source`) and template metadata (`field_id`, `required`, `template_id`). | Integration owner | 2026-11-20 |
| 3 | Choose the transport (function call, files, or HTTP) and the response timeout. | Both owners | 2026-11-24 |
| 4 | Confirm that the claim record and the (`request_id`, `claim_id`) key fit Claim Investigation's input contract, through the Integration–Claim Investigation agreement. | Julian Jiang; Integration owner; Boyu Liu (Claim Investigation) reviews | 2026-11-24 |
| 5 | Confirm the rating-to-outcome mapping in Section 4.2. This also closes IE requirements open item OI-10. | Julian Jiang, Lurui Zheng | 2026-11-17 |
| 6 | Run the Section 7 tests and record the results. | Both owners | 2026-12-04, before Gate 2 (2026-12-07) |

## 9. Change history

Every change to this agreement is a pull request that both owners approve. Both subsystems announce changes in their weekly update in `#bugs26` and tag the other subsystem's members.

| Version | Date | Change | Pull request |
|---|---|---|---|
| Gate 1 draft | 2026-10-18 | Integration → IE input only: raw and structured report, metadata, presence states, six questions for Integration | Not merged (`Input-evaluation` branch, commit `2514238`) |
| Draft for version 1 | 2026-11-10 | Both directions; answers to the six Gate 1 questions; result format, rating-to-outcome mapping, claims, provenance; verification and open items; course template layout | TBD |

## Appendix A. Examples

The repository and issues are fictitious. `fixture-evaluator/1` is an illustrative implementation ID. These examples show the record format and plausible ratings; they are not test results.

### A.1 Structured report record

```json
{
  "schema_version": "1.0",
  "request_id": "req-001",
  "snapshot_id": "snap-123-a",
  "repository": "example/editor",
  "issue_number": 123,
  "issue_url": "https://github.com/example/editor/issues/123",
  "title": "Save dialog reports Error E42",
  "raw_body": "### What happened?\nThe Save dialog shows Error E42 after clicking Save.\n### Steps to reproduce\nOpen a new document, type hello, then click Save.\n### Expected behavior\nThe document should be saved.\n### Version\n2.3.1 on Windows 11.\n### Evidence\nError E42: write failed.\n### Additional details\n",
  "body_source": "initial",
  "labels": ["bug"],
  "created_at": "2026-11-01T14:00:00Z",
  "updated_at": "2026-11-01T14:00:00Z",
  "sections": [
    {"section_id": "s1", "field_id": null, "original_label": "What happened?", "required": null, "status": "provided", "value": "The Save dialog shows Error E42 after clicking Save.", "recognition": "recognized", "semantic_concept": "observed_behavior", "source_lines": {"start": 1, "end": 2}},
    {"section_id": "s2", "field_id": null, "original_label": "Steps to reproduce", "required": null, "status": "provided", "value": "Open a new document, type hello, then click Save.", "recognition": "recognized", "semantic_concept": "steps_to_reproduce", "source_lines": {"start": 3, "end": 4}},
    {"section_id": "s3", "field_id": null, "original_label": "Expected behavior", "required": null, "status": "provided", "value": "The document should be saved.", "recognition": "recognized", "semantic_concept": "expected_behavior", "source_lines": {"start": 5, "end": 6}},
    {"section_id": "s4", "field_id": null, "original_label": "Version", "required": null, "status": "provided", "value": "2.3.1 on Windows 11.", "recognition": "recognized", "semantic_concept": "environment_version", "source_lines": {"start": 7, "end": 8}},
    {"section_id": "s5", "field_id": null, "original_label": "Evidence", "required": null, "status": "provided", "value": "Error E42: write failed.", "recognition": "recognized", "semantic_concept": "supporting_evidence", "source_lines": {"start": 9, "end": 10}},
    {"section_id": "s6", "field_id": null, "original_label": "Additional details", "required": null, "status": "blank", "value": "", "recognition": "unrecognized", "semantic_concept": null, "source_lines": {"start": 11, "end": 12}}
  ],
  "extraction": {"mode": "structured", "template_id": null, "diagnostics": []}
}
```

### A.2 Free-form report record

```json
{
  "schema_version": "1.0",
  "request_id": "req-002",
  "snapshot_id": "snap-124-a",
  "repository": "example/editor",
  "issue_number": 124,
  "issue_url": "https://github.com/example/editor/issues/124",
  "title": "Something is wrong",
  "raw_body": "It does not work. Please help.",
  "body_source": "initial",
  "labels": [],
  "created_at": "2026-11-01T15:00:00Z",
  "updated_at": "2026-11-01T15:00:00Z",
  "sections": [],
  "extraction": {"mode": "free_form", "template_id": null, "diagnostics": []}
}
```

### A.3 Invalid record: `raw_body` missing

Same as A.2 but with `request_id` `"req-003"` and the `raw_body` field removed.

### A.4 Result for A.3

```json
{
  "schema_version": "1.0",
  "request_id": "req-003",
  "snapshot_id": "snap-124-a",
  "processing_status": "invalid_input",
  "criterion_findings": [],
  "unevaluated_criteria": [],
  "claim_extraction": {"status": "not_performed", "reason": "Input failed contract validation."},
  "identified_claims": [],
  "no_checkable_claims": null,
  "diagnostics": [
    {
      "severity": "error",
      "code": "missing_required_field",
      "path": "/raw_body",
      "message": "raw_body is required. An empty string is allowed; omitting the field is not."
    }
  ],
  "provenance": {
    "criteria_version": null,
    "evaluator_version": "fixture-evaluator/1",
    "external_models": [],
    "evaluated_at": "2026-11-10T18:00:00Z"
  }
}
```

### A.5 Completed result for A.1

```json
{
  "schema_version": "1.0",
  "request_id": "req-001",
  "snapshot_id": "snap-123-a",
  "processing_status": "completed",
  "criterion_findings": [
    {
      "criterion_id": "C1",
      "criteria_version": "git:b1820e55e2f5e3a03a8888fad1a4805b3356832b:documentation/bug-report-quality-criteria.md",
      "evaluation_status": "concluded",
      "rating": "P",
      "explanation": "Names the affected component (Save dialog) and the specific failure.",
      "evidence": [
        {"basis": "quotation", "source": "raw_body", "section_id": "s1", "lines": {"start": 2, "end": 2}, "quote": "The Save dialog shows Error E42 after clicking Save.", "explanation": "Component and failure stated."}
      ],
      "unevaluated_reason": null
    },
    {
      "criterion_id": "C2",
      "criteria_version": "git:b1820e55e2f5e3a03a8888fad1a4805b3356832b:documentation/bug-report-quality-criteria.md",
      "evaluation_status": "concluded",
      "rating": "P",
      "explanation": "Gives the actions and input needed to attempt reproduction.",
      "evidence": [
        {"basis": "quotation", "source": "raw_body", "section_id": "s2", "lines": {"start": 4, "end": 4}, "quote": "Open a new document, type hello, then click Save.", "explanation": "Actions and input stated."}
      ],
      "unevaluated_reason": null
    },
    {
      "criterion_id": "C3",
      "criteria_version": "git:b1820e55e2f5e3a03a8888fad1a4805b3356832b:documentation/bug-report-quality-criteria.md",
      "evaluation_status": "concluded",
      "rating": "P",
      "explanation": "States the expected outcome.",
      "evidence": [
        {"basis": "quotation", "source": "raw_body", "section_id": "s3", "lines": {"start": 6, "end": 6}, "quote": "The document should be saved.", "explanation": "Explicit expected result."}
      ],
      "unevaluated_reason": null
    },
    {
      "criterion_id": "C4",
      "criteria_version": "git:b1820e55e2f5e3a03a8888fad1a4805b3356832b:documentation/bug-report-quality-criteria.md",
      "evaluation_status": "concluded",
      "rating": "P",
      "explanation": "States the observed error.",
      "evidence": [
        {"basis": "quotation", "source": "raw_body", "section_id": "s1", "lines": {"start": 2, "end": 2}, "quote": "The Save dialog shows Error E42 after clicking Save.", "explanation": "Observed error stated."}
      ],
      "unevaluated_reason": null
    },
    {
      "criterion_id": "C5",
      "criteria_version": "git:b1820e55e2f5e3a03a8888fad1a4805b3356832b:documentation/bug-report-quality-criteria.md",
      "evaluation_status": "concluded",
      "rating": "P",
      "explanation": "Gives the application version and operating system.",
      "evidence": [
        {"basis": "quotation", "source": "raw_body", "section_id": "s4", "lines": {"start": 8, "end": 8}, "quote": "2.3.1 on Windows 11.", "explanation": "Version and OS stated."}
      ],
      "unevaluated_reason": null
    },
    {
      "criterion_id": "C6",
      "criteria_version": "git:b1820e55e2f5e3a03a8888fad1a4805b3356832b:documentation/bug-report-quality-criteria.md",
      "evaluation_status": "concluded",
      "rating": "P",
      "explanation": "Includes the exact error text.",
      "evidence": [
        {"basis": "quotation", "source": "raw_body", "section_id": "s5", "lines": {"start": 10, "end": 10}, "quote": "Error E42: write failed.", "explanation": "Exact error message is inspectable evidence."}
      ],
      "unevaluated_reason": null
    },
    {
      "criterion_id": "C7",
      "criteria_version": "git:b1820e55e2f5e3a03a8888fad1a4805b3356832b:documentation/bug-report-quality-criteria.md",
      "evaluation_status": "concluded",
      "rating": "P",
      "explanation": "Actions, affected UI, and outcome are specific.",
      "evidence": [
        {"basis": "quotation", "source": "raw_body", "section_id": "s1", "lines": {"start": 2, "end": 2}, "quote": "The Save dialog shows Error E42 after clicking Save.", "explanation": "No vague or undefined terms."}
      ],
      "unevaluated_reason": null
    }
  ],
  "unevaluated_criteria": [],
  "claim_extraction": {"status": "completed", "reason": null},
  "identified_claims": [
    {
      "claim_id": "claim-1",
      "claim_text": "The Save dialog shows Error E42 after clicking Save.",
      "source": {"basis": "quotation", "source": "raw_body", "section_id": "s1", "lines": {"start": 2, "end": 2}, "quote": "The Save dialog shows Error E42 after clicking Save.", "explanation": "Reported behavior that can be checked against the project's code and issues."},
      "named_project_versions": ["2.3.1"],
      "relevant_context": "### What happened?\nThe Save dialog shows Error E42 after clicking Save."
    }
  ],
  "no_checkable_claims": false,
  "diagnostics": [],
  "provenance": {
    "criteria_version": "git:b1820e55e2f5e3a03a8888fad1a4805b3356832b:documentation/bug-report-quality-criteria.md",
    "evaluator_version": "fixture-evaluator/1",
    "external_models": [],
    "evaluated_at": "2026-11-10T18:00:00Z"
  }
}
```

### A.6 Completed result for A.2, with no checkable claims

```json
{
  "schema_version": "1.0",
  "request_id": "req-002",
  "snapshot_id": "snap-124-a",
  "processing_status": "completed",
  "criterion_findings": [
    {
      "criterion_id": "C1",
      "criteria_version": "git:b1820e55e2f5e3a03a8888fad1a4805b3356832b:documentation/bug-report-quality-criteria.md",
      "evaluation_status": "concluded",
      "rating": "M",
      "explanation": "Uses a general term without naming a component or failure.",
      "evidence": [
        {"basis": "quotation", "source": "title", "section_id": null, "lines": null, "quote": "Something is wrong", "explanation": "General term only; no component or failure named."}
      ],
      "unevaluated_reason": null
    },
    {
      "criterion_id": "C2",
      "criteria_version": "git:b1820e55e2f5e3a03a8888fad1a4805b3356832b:documentation/bug-report-quality-criteria.md",
      "evaluation_status": "concluded",
      "rating": "M",
      "explanation": "No reproduction steps.",
      "evidence": [
        {"basis": "absence_check", "source": "whole_report", "section_id": null, "lines": null, "quote": null, "explanation": "Searched the title and body for actions, prerequisites, or inputs; none found."}
      ],
      "unevaluated_reason": null
    },
    {
      "criterion_id": "C3",
      "criteria_version": "git:b1820e55e2f5e3a03a8888fad1a4805b3356832b:documentation/bug-report-quality-criteria.md",
      "evaluation_status": "concluded",
      "rating": "M",
      "explanation": "No expected outcome.",
      "evidence": [
        {"basis": "absence_check", "source": "whole_report", "section_id": null, "lines": null, "quote": null, "explanation": "Searched the title and body for an expected result; none found."}
      ],
      "unevaluated_reason": null
    },
    {
      "criterion_id": "C4",
      "criteria_version": "git:b1820e55e2f5e3a03a8888fad1a4805b3356832b:documentation/bug-report-quality-criteria.md",
      "evaluation_status": "concluded",
      "rating": "M",
      "explanation": "Observed behavior is described only as 'does not work'.",
      "evidence": [
        {"basis": "quotation", "source": "raw_body", "section_id": null, "lines": {"start": 1, "end": 1}, "quote": "It does not work.", "explanation": "General term with no symptom, output, or error."}
      ],
      "unevaluated_reason": null
    },
    {
      "criterion_id": "C5",
      "criteria_version": "git:b1820e55e2f5e3a03a8888fad1a4805b3356832b:documentation/bug-report-quality-criteria.md",
      "evaluation_status": "concluded",
      "rating": "M",
      "explanation": "No software version or environment.",
      "evidence": [
        {"basis": "absence_check", "source": "whole_report", "section_id": null, "lines": null, "quote": null, "explanation": "Searched the title and body for a version, release, commit, or environment; none found."}
      ],
      "unevaluated_reason": null
    },
    {
      "criterion_id": "C6",
      "criteria_version": "git:b1820e55e2f5e3a03a8888fad1a4805b3356832b:documentation/bug-report-quality-criteria.md",
      "evaluation_status": "concluded",
      "rating": "M",
      "explanation": "No supporting material.",
      "evidence": [
        {"basis": "absence_check", "source": "whole_report", "section_id": null, "lines": null, "quote": null, "explanation": "Searched the title and body for error text, logs, screenshots, or other evidence; none found."}
      ],
      "unevaluated_reason": null
    },
    {
      "criterion_id": "C7",
      "criteria_version": "git:b1820e55e2f5e3a03a8888fad1a4805b3356832b:documentation/bug-report-quality-criteria.md",
      "evaluation_status": "concluded",
      "rating": "M",
      "explanation": "Relies on vague terms without defining them.",
      "evidence": [
        {"basis": "quotation", "source": "raw_body", "section_id": null, "lines": {"start": 1, "end": 1}, "quote": "It does not work. Please help.", "explanation": "'Does not work' is not explained."}
      ],
      "unevaluated_reason": null
    }
  ],
  "unevaluated_criteria": [],
  "claim_extraction": {"status": "completed", "reason": null},
  "identified_claims": [],
  "no_checkable_claims": true,
  "diagnostics": [],
  "provenance": {
    "criteria_version": "git:b1820e55e2f5e3a03a8888fad1a4805b3356832b:documentation/bug-report-quality-criteria.md",
    "evaluator_version": "fixture-evaluator/1",
    "external_models": [],
    "evaluated_at": "2026-11-10T18:00:00Z"
  }
}
```

### A.7 Unevaluated criterion (one finding)

The body of this separate report is `Screenshot: https://example.invalid/screenshot.png`. The screenshot is the only evidence, and IE's evidence-access service fails before it can open the link.

```json
{
  "criterion_id": "C6",
  "criteria_version": "git:b1820e55e2f5e3a03a8888fad1a4805b3356832b:documentation/bug-report-quality-criteria.md",
  "evaluation_status": "unevaluated",
  "rating": null,
  "explanation": "A screenshot link is supplied, but IE could not check whether it is accessible or relevant.",
  "evidence": [
    {"basis": "source_reference", "source": "raw_body", "section_id": null, "lines": {"start": 1, "end": 1}, "quote": null, "explanation": "Screenshot link on line 1; not opened because the evidence-access service was unavailable."}
  ],
  "unevaluated_reason": {
    "code": "dependency_unavailable",
    "message": "Evidence-access service unavailable; screenshot not checked."
  }
}
```

The full result has `processing_status: "partial"`, seven findings, `unevaluated_criteria: ["C6"]`, and an `error` diagnostic with code `dependency_unavailable`. If IE had opened the link and found it inaccessible, C6 would instead be a concluded `U`, as the C6 rubric says.

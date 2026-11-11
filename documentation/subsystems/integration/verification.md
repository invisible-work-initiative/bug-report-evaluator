> **Draft**

# Integration Subsystem Verification

This page says how each requirement in [requirements.md](requirements.md) is verified, and which test does it. Status is from `python -m pytest -q` on branch `integration-prototype`, 2026-11-11: 87 passed, 0 failed.

Test files are in `tests/`. Tests use the placeholder stubs for Input Evaluation (IE) and Claim Investigation (CI), or small fakes that record what they receive.

## Verification table

| INT | Method | Procedure | Test file and functions | Status |
|---|---|---|---|---|
| INT-1 | Test | Submit a sample report by paste, upload and GitHub issue URL. Check that Integration receives it unchanged. Check that empty bodies, pull requests and bad URLs are refused. | `tests/test_int_1.py`: `test_sample_report_is_received_verbatim`, `test_crlf_is_kept_and_title_is_hashed`, `test_each_submission_gets_its_own_id`, `test_empty_body_is_refused`, `test_github_issue_is_fetched`, `test_pull_request_is_rejected`, `test_bad_url_is_rejected`, `test_non_object_answer_is_rejected`. `tests/test_web.py`: `test_evaluate_html_result`, `test_all_samples_via_both_endpoints`, `test_github_issue_source` | Pass |
| INT-2 | Test | Structure the sample reports. Check that every section is an exact slice of the original body, and that nothing is added. Check that a wrong span is caught. | `tests/test_int_2.py`: `test_span_invariant_on_samples`, `test_good_report`, `test_missing_steps_sample`, `test_adversarial_cases`, `test_explicit_title_is_kept_and_nothing_is_derived`, `test_unmapped_sections`, `test_comment_only_section_is_not_meaningful`, `test_line_numbers`, `test_issue_form_fixtures`, `test_regex_fixes`, `test_verify_catches_a_wrong_span` | Pass |
| INT-3 | Test | Run the pipeline with a recording evaluator. Check that it gets both the `RawReport` and the `StructuredReport`. | `tests/test_int_3.py`: `test_ie_receives_original_and_structured` | Pass |
| INT-4 | Test | Run the pipeline with a recording investigator. Check that it gets the request with report context. Check the routing rule: CI is skipped unless the decision is `investigate` and there is at least one request. Check that a request for another report is refused. | `tests/test_int_4.py`: `test_ci_receives_request_with_context`, `test_report_id_mismatch_is_rejected`, `test_uc2_ci_skipped_unless_investigate`, `test_uc3_ci_skipped_without_requests` | Pass |
| INT-5 | Test | Run with fake IE and CI that each return findings. Check that the collected list has both. | `tests/test_int_5.py`: `test_findings_from_both_subsystems` | Pass |
| INT-6 | Test | Check that the output has the collected findings and `could_not_check`, and that it reaches the maintainer through the HTML and JSON endpoints. | `tests/test_int_6.py`: `test_output_includes_collected_findings_and_r4`, `test_output_reaches_maintainer_interface`. `tests/test_web.py`: `test_evaluate_html_result`, `test_xss_is_escaped_everywhere`, `test_api_errors_are_json` | Pass |
| INT-7 | Test | Check that every finding, request and evidence item carries the right `report_id`. Check that a finding or request for another report is refused. | `tests/test_int_7.py`: `test_everything_links_to_its_report`, `test_finding_for_another_report_is_rejected`, `test_request_for_another_report_is_rejected` | Pass |
| INT-8 | Test | Pass findings with evidence from both subsystems. Check that the evidence in the output is equal to what was sent. | `tests/test_int_8.py`: `test_evidence_unchanged_from_both_subsystems` | Pass |
| INT-9 | Inspection | Follow the checklist below. Automated checks support it but do not replace it. | Supporting tests in `tests/test_int_9.py`: `test_no_model_has_an_identity_field`, `test_output_has_no_identity_keys`, `test_github_user_never_reaches_a_model`, `test_two_submissions_share_no_identifier`, `test_runner_turns_access_log_off`, `test_code_neither_logs_nor_writes_files`; `tests/test_int_1.py`: `test_received_github_report_has_no_author` | Pass (tests); inspection not yet signed off |

## INT-9 inspection checklist

Inspect the code on the branch under review. Record the reviewer, the date and the commit.

- [ ] No model in `src/bugs26/integration/models.py` has a field for a reporter, author, user, login, email, IP address or session. Check `RawReport`, `StructuredReport`, `Finding`, `InvestigationRequest`, `IEResult`, `CIResult` and `MaintainerOutput`.
- [ ] `src/bugs26/integration/github.py` returns only `title`, `body`, `issue_url` and `repo_url`. The GitHub `user` object, and every other field in the API answer, is dropped.
- [ ] No identifier is shared between two submissions. `report_id` is a new random UUID for each submission.
- [ ] No code writes to disk or to a database. Search `src/` for `open(`, `sqlite`, `pickle`, `shelve` and file writes.
- [ ] No code logs. Search `src/` for `logging`, `print` and `logger`.
- [ ] No cache or global holds reports between requests.
- [ ] `src/bugs26/web/__main__.py` starts uvicorn with `access_log=False`. Start the server with `python -m bugs26.web`, send a request, and check that no request line is printed.
- [ ] The JSON download on the result page is a `data:` link. The server keeps nothing.
- [ ] The placeholder IE and CI stubs add no identity fields. Real IE and CI code must be inspected the same way when it replaces them.

## Not yet covered

- Real IE and CI code. All tests use stubs or fakes. The tests named in the two interface agreements must be re-run against the real code.
- Timeouts and failures inside IE or CI. No test covers a stub that raises or hangs.

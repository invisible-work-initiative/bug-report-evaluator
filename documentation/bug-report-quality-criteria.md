# Bug Report Quality Criteria Calibration

Input Evaluation Subsystem  |  Gate 1

## Purpose

This document defines candidate criteria for evaluating the quality of incoming bug reports. Two evaluators will independently apply the criteria to the same set of reports, compare disagreements, and revise the definitions using report evidence and relevant research.

Assessment scope: only information contained in the initial issue submission will be evaluated. Information added later through comments will not be counted as part of the original report.

### Calibration Workflow

Select reports -> score independently -> compare disagreements -> discuss definitions -> revise criteria using report evidence and relevant research.

## Rating Scale

| Rating | Definition |
| --- | --- |
| P — Present | The information is provided and satisfies the criterion's operational definition. |
| M — Missing or Insufficient | The criterion applies, but the required information is absent or insufficient. |
| N/A — Not Applicable | The criterion does not apply to this type of report. Absence alone does not justify an N/A rating. |
| U — Unclear | Contradictory or uninterpretable information prevents a reliable assessment. |

### Rating Decision Order

| Order | Decision | Rating |
| --- | --- | --- |
| 1 | The criterion does not apply to the report. | N/A |
| 2 | The criterion applies, but the information is absent or insufficient. | M |
| 3 | The information is contradictory or cannot be interpreted reliably. | U |
| 4 | The information satisfies the operational definition. | P |

If an evaluator can identify what information is missing, the appropriate rating is M, not U. The U rating is reserved for information that is contradictory or too ambiguous to support a reliable judgment.

## Candidate Criteria

| ID | Criterion | Operational definition |
| --- | --- | --- |
| C1 | Bug description | Identifies the affected feature or component and describes the reported failure or incorrect behavior. |
| C2 | Steps to reproduce | Provides the actions, prerequisites, and inputs needed for another person to attempt to trigger the reported behavior without requesting additional procedural information. For a static defect, a precise and directly inspectable location is sufficient. |
| C3 | Expected behavior | States the outcome that should occur under the reported conditions and distinguishes it from the observed behavior. |
| C4 | Observed behavior | States the actual result, symptom, output, or error that occurred under the reported conditions. |
| C5 | Environment and version | Identifies the affected software version, release, or commit. When behavior could depend on the operating system, hardware, browser, runtime, extension, dependency, or configuration, the applicable environmental details are also provided. |
| C6 | Supporting evidence | Provides inspectable material that directly supports the reported behavior when such material can reasonably be captured. Evidence may include exact error text, stack traces, logs, screenshots, recordings, sample input and output, performance measurements, or precise code and documentation references. |
| C7 | Clarity and specificity | Describes the relevant actions, objects, conditions, and outcomes precisely enough for the reported problem to be understood without guessing the meaning of vague or undefined terms. Minor language or grammar errors do not cause failure when the intended meaning remains clear. |

## Criterion Rating Guidance

### C1  Bug Description

| Rating | Decision rule |
| --- | --- |
| P | The report identifies both the affected feature or component and the specific failure or incorrect behavior. |
| M | The affected feature is not identified, or the report uses a general term such as 'broken' or 'wrong' without describing the failure. |
| N/A | This criterion normally applies to every bug report. |
| U | The description is contradictory or cannot be interpreted well enough to determine what problem is being reported. |

## Criterion Rating Guidance Continued

### C2  Steps to Reproduce

| Rating | Decision rule |
| --- | --- |
| P | Another person could attempt to trigger the behavior using the supplied actions, prerequisites, and inputs without requesting essential procedural information. |
| M | Reproduction information is absent or lacks a required action, prerequisite, configuration, or input. |
| N/A | The issue is a static defect and the report provides a precise file, code location, documentation page, or other directly inspectable location. |
| U | The supplied steps contradict one another or do not establish an interpretable sequence of actions. |

## Criterion Rating Guidance Continued

### C3  Expected Behavior

| Rating | Decision rule |
| --- | --- |
| P | The report clearly states what should happen under the reported conditions. |
| M | The expected result is absent or expressed only through a general statement such as 'it should work.' |
| N/A | The correct result is established by a precise reference to an applicable specification, requirement, or documentation source, making a separate statement unnecessary. |
| U | The report presents conflicting expected outcomes, and the intended result cannot be determined reliably. |

## Criterion Rating Guidance Continued

### C4  Observed Behavior

| Rating | Decision rule |
| --- | --- |
| P | The report clearly states what occurred, such as an incorrect output, error, crash, missing response, or other observable behavior. |
| M | The actual result is absent or described only with a general term such as 'wrong,' 'broken,' or 'does not work.' |
| N/A | This criterion normally applies to every bug report. |
| U | The report presents conflicting accounts of the observed behavior, and the actual result cannot be determined reliably. |

## Criterion Rating Guidance Continued

### C5  Environment and Version

| Rating | Decision rule |
| --- | --- |
| P | The report identifies the affected software version, release, or commit and includes any environmental details needed to place the behavior in context. |
| M | The software version is absent, or environmental information needed to understand or reproduce the problem is missing. |
| N/A | Version and runtime environment clearly do not affect assessment of the issue, such as a visible documentation error at a precise location. |
| U | The supplied version or environment details conflict with one another, so the affected context cannot be determined reliably. |

## Criterion Rating Guidance Continued

### C6  Supporting Evidence

| Rating | Decision rule |
| --- | --- |
| P | The report includes at least one inspectable item that directly supports the reported behavior. |
| M | Supporting evidence could reasonably be provided for this type of problem, but it is absent or insufficient. |
| N/A | The issue can be assessed directly from a precise code or documentation location and does not require separate logs, screenshots, or output. |
| U | An attachment or link is inaccessible, or the relationship between the supplied material and the reported problem cannot be determined reliably. |

## Criterion Rating Guidance Continued

### C7  Clarity and Specificity

| Rating | Decision rule |
| --- | --- |
| P | The relevant objects, actions, conditions, and outcomes can be understood without unsupported assumptions. |
| M | The report relies on vague terms such as 'broken,' 'slow,' 'wrong,' or 'does not work' without explaining their specific meaning. |
| N/A | This criterion normally applies to every bug report. |
| U | The report is internally contradictory or too difficult to interpret for the evaluator to determine the intended meaning reliably. |

## Supporting Evidence Guidelines

| Type of reported problem | Evidence normally expected |
| --- | --- |
| Error or crash | Exact error message, stack trace, crash report, or relevant log |
| Visual or user-interface defect | Screenshot or screen recording |
| Incorrect output | Sample input and actual output, preferably with the expected output |
| Performance problem | Timing, memory, or other measurements and an appropriate comparison baseline |
| Intermittent problem | Relevant logs, occurrence frequency, or known triggering conditions |
| Static code or documentation defect | Precise file, page, code location, or direct link |
| Data-dependent problem | Minimal example data or instructions for generating representative test data |

These guidelines establish normal expectations rather than absolute requirements. Evaluators should record exceptions and use them during calibration to determine whether a criterion definition needs revision.

## Overall Assessment

After rating all seven criteria, each evaluator records an overall recommendation. During initial calibration, the overall decision should not be calculated automatically from the number of Present ratings.

| Field | Permitted values or required content |
| --- | --- |
| Overall decision | Investigate / Request More Information / Do Not Investigate |
| Missing information request | A specific description of the information the reporter should provide, or N/A |
| Confidence | High / Medium / Low |
| Reason | One or two sentences explaining the overall decision |
| Evidence scope | Initial issue submission only |
| Evaluator | Evaluator's name |
| Assessment date | Date on which the assessment was completed |

## Independent Assessment Procedure

1. Both evaluators use the same report IDs and source URLs.
1. Each evaluator completes all ratings independently without viewing the other evaluator's results.
1. The evaluators compare their completed ratings.
1. Each disagreement is recorded with the reason for the difference.
1. The evaluators agree on a final rating or identify an unresolved issue.
1. Criterion definitions are retained, revised, or removed based on report evidence and relevant research.
1. Each final definition is documented with at least one supporting report example or research source.

Use the same report IDs and source URLs in both assessment tables. Enter P, M, N/A, or U in every applicable criterion cell. Present means that the initial report supplies the required information; it does not mean that the reported bug has been independently verified.

## Julian Assessment

Existing ratings from the original workbook are preserved below. They should remain unchanged until the independent comparison stage.

| ID | Source URL | C1 | C2 | C3 | C4 | C5 | C6 | C7 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 01 | [https://github.com/microsoft/vscode/issues/216653](https://github.com/microsoft/vscode/issues/216653) | P | P | P | P | P | P | P |
| 02 | [https://github.com/microsoft/vscode/issues/331206](https://github.com/microsoft/vscode/issues/331206) | P | P | U | P | M | P | P |
| 03 | [https://github.com/microsoft/vscode/issues/331110](https://github.com/microsoft/vscode/issues/331110) | P | M | U | P | M | M | P |
| 04 | [https://github.com/pandas-dev/pandas/issues/58971](https://github.com/pandas-dev/pandas/issues/58971) | P | P | U | P | P | P | U |
| 05 | [https://github.com/pandas-dev/pandas/issues/54199](https://github.com/pandas-dev/pandas/issues/54199) | P | P | P | P | P | P | P |
| 06 | [https://github.com/pandas-dev/pandas/issues/37716](https://github.com/pandas-dev/pandas/issues/37716) | P | U | P | P | M | U | P |
| 07 | [https://github.com/home-assistant/core/issues/176602](https://github.com/home-assistant/core/issues/176602) | P | P | P | P | P | P | P |
| 08 | [https://github.com/home-assistant/core/issues/142190](https://github.com/home-assistant/core/issues/142190) | P | M | U | P | P | M | P |
| 09 | [https://github.com/react/react/issues/22718](https://github.com/react/react/issues/22718) | P | P | P | P | P | P | P |
| 10 | [https://github.com/tensorflow/tensorflow/issues/127778](https://github.com/tensorflow/tensorflow/issues/127778) | P | P | M | P | P | P | P |

## Lurui Assessment

Complete this table independently before reviewing Julian's ratings. Use only the information in each issue's initial submission.

| ID | Source URL | C1 | C2 | C3 | C4 | C5 | C6 | C7 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 01 | [https://github.com/microsoft/vscode/issues/216653](https://github.com/microsoft/vscode/issues/216653) | P | P | P | P | P | P | P |
| 02 | [https://github.com/microsoft/vscode/issues/331206](https://github.com/microsoft/vscode/issues/331206) | P | P | M | P | M | P | P |
| 03 | [https://github.com/microsoft/vscode/issues/331110](https://github.com/microsoft/vscode/issues/331110) | P | M | M | P | M | M | P |
| 04 | [https://github.com/pandas-dev/pandas/issues/58971](https://github.com/pandas-dev/pandas/issues/58971) | P | P | U | P | P | P | U |
| 05 | [https://github.com/pandas-dev/pandas/issues/54199](https://github.com/pandas-dev/pandas/issues/54199) | P | P | P | P | P | P | P |
| 06 | [https://github.com/pandas-dev/pandas/issues/37716](https://github.com/pandas-dev/pandas/issues/37716) | P | P | P | P | M | P | P |
| 07 | [https://github.com/home-assistant/core/issues/176602](https://github.com/home-assistant/core/issues/176602) | P | P | P | P | P | P | P |
| 08 | [https://github.com/home-assistant/core/issues/142190](https://github.com/home-assistant/core/issues/142190) | P | M | M | P | P | M | P |
| 09 | [https://github.com/react/react/issues/22718](https://github.com/react/react/issues/22718) | P | P | P | P | M | P | P |
| 10 | [https://github.com/tensorflow/tensorflow/issues/127778](https://github.com/tensorflow/tensorflow/issues/127778) | P | P | M | P | P | P | P |

## Calibration Record

Record only ratings that differ. Explain why the evaluators interpreted the report differently, then document the agreed rating, a definition change, or an unresolved question.

| Report ID | Criterion | Evaluator 1 | Evaluator 2 | Reason for difference | Decision or change |
| --- | --- | --- | --- | --- | --- |
| 02 | C3 | U | M | The desired scope is implied by the title, but the initial report does not explicitly state the expected outcome. The missing information is identifiable. | Use M. Missing or merely implied expected behavior is not U. |
| 03 | C3 | U | M | The report says the tool is 'slower than expected' but gives no explicit expected latency or outcome. The expected result is missing, not contradictory. | Use M. Reserve U for conflicting or uninterpretable expectations. |
| 06 | C2 | U | P | The initial report provides an accessible example archive, identifies the input, and supplies the melt command needed to attempt reproduction. | Use P. An accessible minimal example may provide required input and prerequisites. |
| 06 | C6 | U | P | The attached example archive is an inspectable artifact directly connected to the reported overwrite behavior. | Use P. Accessible attachments count as supporting evidence. |
| 08 | C3 | U | M | The report states that the devices 'do not work anymore' but does not state the expected behavior. The omission is clear. | Use M. An absent expected outcome is missing information. |
| 09 | C5 | P | M | React 17.0.2 is supplied, but browser and operating-system information are absent even though DOM event behavior may depend on the runtime environment. | Use M. Require relevant browser or runtime details for DOM-event reports. |

## Final Criteria Decisions

| Criterion | Keep / Revise / Remove | Final definition | Evidence or source | Verification rule |
| --- | --- | --- | --- | --- |
| C1 | Keep | Identifies the affected feature or component and describes the specific failure or incorrect behavior. | Reports 01-10; no C1 disagreement | P requires both the affected component and a specific failure; otherwise M, unless contradictory. |
| C2 | Revise | Provides the actions, prerequisites, and inputs needed to attempt reproduction. A precise static location or an accessible minimal example may supply the needed input. | Report 06; Calibration Record | P if another person can attempt reproduction without requesting essential procedural information. |
| C3 | Revise | States the outcome that should occur under the reported conditions. An implied preference or a general statement is insufficient. | Reports 02, 03, and 08 | P for an explicit expected outcome; M if absent or only implied; U only if expectations conflict. |
| C4 | Keep | States the actual result, symptom, output, or error that occurred under the reported conditions. | Reports 01-10; no C4 disagreement | P requires a distinct observable result; vague terms without a symptom are M. |
| C5 | Revise | Identifies the affected software version and any operating system, browser, runtime, dependency, or configuration details relevant to the behavior. | Report 09; Calibration Record | Require a version and every environment detail reasonably capable of affecting the issue. |
| C6 | Revise | Provides accessible, inspectable material that directly supports the reported behavior when such evidence can reasonably be captured. Accessible attachments count. | Report 06; Calibration Record | P for relevant accessible evidence; M if reasonably available but absent; U if inaccessible or unrelated. |
| C7 | Keep | Describes relevant actions, objects, conditions, and outcomes precisely enough to be understood without unsupported assumptions. | Reports 01-10; no new definition needed | P when meaning is clear despite minor language errors; vague unexplained terms are M. |

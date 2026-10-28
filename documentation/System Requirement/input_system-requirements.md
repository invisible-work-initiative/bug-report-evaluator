# Input Evaluation Subsystem Requirements

**Milestone:** Gate 2 Revision  
**Status:** Final Draft for Baseline Review

---

# 1. Purpose and Scope

The Input Evaluation subsystem evaluates incoming bug reports against the published quality criteria, identifies checkable claims, preserves information required for traceability and downstream investigation, and produces outputs that support system-level evaluation.

This document specifies **what the Input Evaluation subsystem is required to accomplish**.

Implementation choices such as subsystem routing, identifiers, data schemas, algorithms, model selection, prompts, storage mechanisms, and concrete field names are treated as **design or interface decisions**, not subsystem requirements.

---

# 2. Definitions

An **input report** is a bug report received by the Input Evaluation subsystem.

An **accepted report** is an input report that satisfies all conditions designated as required for evaluation by the approved Input Evaluation input-interface contract.

A **criterion finding** is the evaluation outcome for one published quality criterion.

An **evidence basis** is inspectable information from the originating report, or an inspectable determination that information required by a criterion is absent.

An **unevaluated criterion** is a quality criterion for which the subsystem cannot produce a substantive evaluation conclusion from the available input.

An **identified claim** is a checkable claim recognized in an input report for downstream investigation.

An **investigation package** consists of an identified claim and the report information required by the approved downstream interface contract for that claim to be interpreted and investigated.

**Traceability** is the ability to associate an output unambiguously with the originating report and source content from which it was derived.

A **contract-invalid input** is an input that does not satisfy one or more conditions designated as required by the approved Input Evaluation input-interface contract.

A **style-variation pair** consists of two reports with the same intended technical content but different formatting, grammar, or writing style.

An **identity-variation pair** consists of two reports with the same technical content but different reporter-identifying information.

---

# 3. Subsystem Requirements

The IE1–IE7 headings organize the major Input Evaluation capabilities.

Each numbered requirement represents one independently verifiable subsystem obligation.

---

# IE1 — Criterion Evaluation

## IE1.1 — Criterion Coverage

### Requirement

For each accepted report, the Input Evaluation subsystem shall produce exactly one criterion finding for every published quality criterion.

### Rationale

The published criteria collectively define the required bug-report quality evaluation. Missing a criterion produces an incomplete evaluation, while duplicate findings for the same criterion can create ambiguity.

### Source

R1 — The system shall evaluate every incoming bug report against the quality criteria.

### Verification Method

Test

### Verification

Process representative accepted reports and compare the generated criterion findings with the published quality-criterion list.

### Acceptance Criterion

For each accepted verification report:

- 100% of published quality criteria shall be represented; and
- each criterion shall have exactly one corresponding finding.

---

## IE1.2 — Finding Evidence

### Requirement

Each criterion finding shall include an inspectable evidence basis traceable to the originating report.

### Rationale

A finding must have an inspectable basis so that its conclusion can be reviewed rather than treated as an unsupported assertion. This applies both when relevant information is present and when a finding is based on the absence of required information.

### Source

R3 — Every finding shall cite the evidence that supports it, in a form the maintainer can inspect.

### Verification Method

Inspection / Test

### Verification

Inspect criterion findings from representative reports and determine whether each finding contains an evidence basis that can be associated with the originating report.

### Acceptance Criterion

100% of criterion findings shall contain an inspectable evidence basis traceable to the correct originating report.

---

## IE1.3 — Unevaluated Criterion Reporting

### Requirement

For each accepted report, the Input Evaluation subsystem shall identify every unevaluated quality criterion and provide a reason for each unevaluated criterion.

### Rationale

An inability to evaluate a criterion is different from determining that the criterion is satisfied, missing, insufficient, or not applicable. Explicit reporting prevents an unevaluated criterion from being mistaken for a valid evaluation result.

### Source

R4 — Every system output shall state what the system could not check.

### Verification Method

Test

### Verification

Process reports intentionally constructed so that selected criteria cannot be evaluated.

### Acceptance Criterion

100% of intentionally unevaluated criteria shall be explicitly identified with a reason.

---

# IE2 — Checkable Claim Identification

## IE2.1 — Claim Identification Recall

### Requirement

The Input Evaluation subsystem shall achieve a claim recall of at least 80% on the approved human-labeled historical claim-evaluation set.

### Rationale

Downstream investigation can investigate only claims that Input Evaluation successfully identifies. A recall threshold establishes a measurable minimum level of claim-identification coverage without prescribing how claims are identified.

### Source

Derived subsystem requirement — pending explicit system-level allocation.

### Verification Method

Analysis / Test

### Verification

Run Input Evaluation on the approved human-labeled historical claim-evaluation set.

Compare identified claims with reference claims using the approved claim-matching rule.

Calculate:

**Claim Recall = Matched Reference Claims / Total Reference Claims**

### Acceptance Criterion

Claim recall shall be greater than or equal to 80%.

### Baseline Note

The 80% threshold is the current subsystem draft target and requires system-level approval before formal baselining.

---

# IE3 — Claim Traceability

## IE3.1 — Claim Traceability

### Requirement

Each identified claim produced at the Input Evaluation subsystem boundary shall be unambiguously traceable to its originating report and source content.

### Rationale

A report may contain multiple claims, and those claims may later be processed by multiple subsystems. Traceability prevents claims from being confused, detached from their original context, or associated with the wrong report.

### Source

Derived subsystem requirement — pending explicit system-level allocation.

### Verification Method

Inspection / Test

### Verification

Process reports containing multiple claims and attempt to associate every identified claim with its originating report and source content using only information available at the Input Evaluation subsystem boundary.

### Acceptance Criterion

100% of identified claims shall be traceable to the correct originating report and source content.

---

# IE4 — Downstream Output Availability

## IE4.1 — Criterion Finding Availability

### Requirement

The Input Evaluation subsystem shall make every generated criterion finding available at its downstream subsystem boundary.

### Rationale

Criterion findings cannot contribute to downstream system processing or the maintainer-facing output if they remain internal to Input Evaluation.

### Source

Derived from R2 through subsystem allocation.

R2 — The system shall present the findings for each report to the maintainer.

### Verification Method

Interface Test

### Verification

Compare the criterion findings generated internally by Input Evaluation with the findings exposed at the downstream subsystem boundary.

### Acceptance Criterion

100% of generated criterion findings shall be available at the downstream subsystem boundary.

---

## IE4.2 — Investigation Package Availability

### Requirement

The Input Evaluation subsystem shall make one investigation package available at its downstream subsystem boundary for every identified claim.

### Rationale

Claim identification has no downstream value if the identified claim and the information required for investigation cannot leave the subsystem.

Defining the required contents through the approved interface contract avoids embedding design-specific fields in the behavioral requirement.

### Source

Derived subsystem requirement — pending explicit system-level allocation.

### Verification Method

Interface Test

### Verification

Process reports containing multiple identified claims and compare the internally identified claims with the investigation packages exposed at the downstream subsystem boundary.

### Acceptance Criterion

100% of identified claims shall have a corresponding investigation package that satisfies the approved downstream interface contract.

---

# IE5 — Input Robustness

## IE5.1 — Contract-Invalid Input Handling

### Requirement

For each contract-invalid input, the Input Evaluation subsystem shall return an explicit non-normal processing outcome instead of reporting a normally completed evaluation.

### Rationale

Malformed or unsupported inputs must not produce normal-looking outputs that could be mistaken for valid evaluations.

This requirement makes invalid processing visible without prescribing a particular error format or implementation mechanism.

### Source

Derived subsystem requirement — pending explicit system-level robustness allocation.

### Verification Method

Interface Test / Test

### Verification

Submit verification inputs that intentionally violate required conditions of the approved input-interface contract.

### Acceptance Criterion

100% of contract-invalid verification inputs shall produce an explicit non-normal processing outcome and shall not be reported as normally completed evaluations.

---

## IE5.2 — Style-Variation Robustness

### Requirement

The Input Evaluation subsystem shall achieve criterion-finding agreement at or above the approved style-variation threshold on the approved style-variation test set.

### Rationale

Criterion findings should depend primarily on the technical content of a bug report rather than superficial differences in grammar, formatting, or writing style.

### Source

Derived subsystem requirement — pending explicit system-level robustness allocation.

### Verification Method

Analysis / Test

### Verification

Evaluate the approved style-variation pairs under the same evaluation configuration and calculate criterion-level agreement using the approved comparison rule.

### Acceptance Criterion

Criterion-level agreement shall be greater than or equal to the approved style-variation threshold.

### TBR

**TBR-IE-01:** Style-variation agreement threshold.

This value must be approved before formal verification.

---

# IE6 — Reporter Privacy and Identity Independence

## IE6.1 — Cross-Report Reporter Privacy

### Requirement

The Input Evaluation subsystem shall not create or retain a cross-report reporter profile based on reporter identity.

### Rationale

Input Evaluation is intended to evaluate bug-report content rather than contributor history. Reporter profiling is unnecessary for this function and may introduce privacy concerns or reporter-specific treatment.

### Source

R6 — The system shall not compile information about individual people across reports.

### Verification Method

Inspection / Test

### Verification

Process multiple reports, including multiple reports from the same contributor, and inspect Input Evaluation outputs, persistent state, and subsystem-controlled records within the approved verification scope.

### Acceptance Criterion

No inspected Input Evaluation artifact shall contain a cross-report reporter profile based on reporter identity.

---

## IE6.2 — Reporter Identity Independence

### Requirement

The Input Evaluation subsystem shall achieve criterion-finding agreement at or above the approved identity-independence threshold on the approved identity-variation test set.

### Rationale

Bug-report quality should be evaluated from report content rather than reporter identity.

### Source

Derived from R6 — pending system-level approval.

### Verification Method

Analysis / Test

### Verification

Evaluate approved identity-variation pairs under the same evaluation configuration and compare their criterion findings.

### Acceptance Criterion

Criterion-level agreement shall be greater than or equal to the approved identity-independence threshold.

### TBR

**TBR-IE-02:** Identity-independence agreement threshold.

This value must be approved before formal verification.

---

# IE7 — Evaluation Support and Provenance

## IE7.1 — Historical Evaluation Comparability

### Requirement

Each criterion finding generated for the approved historical evaluation set shall be unambiguously matchable to the corresponding human-labeled reference unit required by the approved system evaluation procedure.

### Rationale

System-level accuracy and other evaluation metrics cannot be calculated unless subsystem outputs can be associated consistently with the corresponding human reference results.

### Source

Derived from R5.

R5 — The system shall be more accurate than the baseline in the historical evaluation.

### Verification Method

Analysis / Test

### Verification

Run Input Evaluation on the approved historical evaluation set and attempt to match every criterion finding with the corresponding human-labeled reference unit.

### Acceptance Criterion

100% of criterion findings generated for accepted historical-evaluation reports shall be matchable to their corresponding reference units.

---

## IE7.2 — Criteria-Version Provenance

### Requirement

Each completed Input Evaluation result shall identify the quality-criteria version used to produce the result.

### Rationale

Evaluation behavior may change when quality-criterion definitions change. Recording the criteria version supports reproducibility, interpretation of historical results, debugging, and comparison between system versions.

### Source

Derived subsystem requirement — pending explicit system-level provenance allocation.

### Verification Method

Inspection / Test

### Verification

Inspect representative completed Input Evaluation results and determine the quality-criteria version used to generate each result.

### Acceptance Criterion

The quality-criteria version shall be determinable for 100% of completed verification results.

---

## IE7.3 — External-Model Provenance

### Requirement

Each completed Input Evaluation result produced using an external model shall identify the external model configuration required by the approved provenance definition.

### Rationale

Evaluation behavior may change when the external model or its configuration changes. Recording model provenance supports reproducibility, debugging, interpretation of historical results, and comparison between evaluation runs.

### Source

Derived subsystem requirement — pending explicit system-level provenance allocation.

### Verification Method

Inspection / Test

### Verification

Inspect representative completed results generated using an external model and determine whether the required model configuration can be identified.

### Acceptance Criterion

The required external-model configuration shall be determinable for 100% of applicable verification results.

---

# 4. Design and Interface Decisions

The following are current architecture, design, or interface decisions and are intentionally **not subsystem requirements**.

| Design / Interface Decision | Requirement Supported |
|---|---|
| Assign a unique `claim_id` to each identified claim. | IE3.1 |
| Preserve the exact claim text in the downstream interface record. | IE3.1 |
| Preserve a source-report reference. | IE3.1 |
| Define required investigation-context fields in the downstream interface contract. | IE4.2 |
| Route current Input Evaluation outputs through Integration. | IE4.1, IE4.2 |
| Current downstream architecture is Input Evaluation → Integration → Claim Investigation. | IE4.1, IE4.2 |
| Use an agreed structured representation for subsystem inputs and outputs. | IE4, IE5 |
| Define concrete representations for non-normal processing outcomes. | IE5.1 |
| Select the model, prompt, algorithm, or software implementation used to perform evaluation. | Implementation |
| Define concrete provenance field names. | IE7.2, IE7.3 |

A design decision may change without changing the underlying requirement, provided the replacement design continues to satisfy that requirement.

---

# 5. Verification Assets Required Before Formal Verification

The following assets shall be approved or baselined before the associated requirements are formally verified:

1. published quality-criterion set;
2. quality-criteria version definition;
3. Input Evaluation input-interface contract;
4. downstream interface contract;
5. human-labeled historical criterion-evaluation set;
6. human-labeled historical claim-evaluation set;
7. claim-matching rule;
8. style-variation test set;
9. identity-variation test set;
10. criterion-finding comparison rule;
11. historical system-evaluation procedure;
12. provenance definition;
13. applicable performance thresholds.

---

# 6. Traceability Summary

## Current System Requirements

| System Requirement | Input Evaluation Allocation |
|---|---|
| R1 — Evaluate every incoming bug report against the quality criteria | IE1.1 |
| R2 — Present findings for each report to the maintainer | IE4.1 |
| R3 — Every finding shall cite inspectable evidence | IE1.2 |
| R4 — Every system output shall state what could not be checked | IE1.3 |
| R5 — The system shall be more accurate than the baseline in historical evaluation | IE7.1 |
| R6 — The system shall not compile information about individual people across reports | IE6.1; IE6.2 is derived |

## Derived Requirements Pending Explicit System-Level Allocation

The following requirements do not yet map to an explicit numbered requirement in the current system-requirements artifact:

- IE2.1 — Claim Identification Recall
- IE3.1 — Claim Traceability
- IE4.2 — Investigation Package Availability
- IE5.1 — Contract-Invalid Input Handling
- IE5.2 — Style-Variation Robustness
- IE6.2 — Reporter Identity Independence
- IE7.2 — Criteria-Version Provenance
- IE7.3 — External-Model Provenance

These requirements shall remain identified as **derived subsystem requirements** until their system-level allocation is formally approved.

---

# 7. Open Decisions Before Baseline

## OD-1 — Claim Recall Threshold

Confirm whether the current 80% claim-recall target is approved as the subsystem performance threshold.

---

## OD-2 — Claim Precision / False Positives

Determine whether Input Evaluation requires an additional claim-precision or false-positive requirement.

No threshold shall be introduced until the corresponding system-level need is agreed.

---

## OD-3 — Style-Variation Threshold

Approve the threshold required for IE5.2.

Reference: **TBR-IE-01**.

---

## OD-4 — Identity-Independence Threshold

Approve the threshold required for IE6.2.

Reference: **TBR-IE-02**.

---

## OD-5 — System Requirement Allocation

Determine whether the derived claim-identification, traceability, robustness, identity-independence, and provenance requirements require explicit system-level requirements or formal subsystem allocation.

---

## OD-6 — Interface Baseline

Finalize and approve the upstream and downstream Input Evaluation interface contracts before formal interface verification.

---

# 8. Requirement–Design Separation

A **requirement** describes an externally observable capability, constraint, or measurable performance outcome that must remain true regardless of the implementation selected.

Examples:

- achieve the approved claim-recall threshold;
- preserve claim traceability;
- produce one finding per criterion;
- prevent contract-invalid input from appearing as a normally completed evaluation.

A **design decision** describes how the subsystem satisfies a requirement.

Examples:

- assign a `claim_id`;
- use JSON;
- use an LLM;
- use a particular prompt;
- use Python;
- route outputs through Integration.

A statement should normally remain outside the subsystem requirements if it could change solely because the implementation changes while the required subsystem behavior remains unchanged.
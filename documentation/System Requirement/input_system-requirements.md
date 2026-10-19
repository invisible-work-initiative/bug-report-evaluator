# Input Evaluation Subsystem Requirements

**Milestone:** Gate 1  
**Status:** Draft subsystem requirements and verification plan

## 1. Scope

The Input Evaluation subsystem evaluates the quality of incoming bug reports, identifies checkable claims, preserves the report information required for downstream investigation, and provides criterion findings and investigation requests to the Integration subsystem.

The confirmed downstream subsystem flow is:

Input Evaluation → Integration → Claim Investigation

Input Evaluation does not directly transfer investigation requests to Claim Investigation.

The direct upstream interface to Input Evaluation remains to be confirmed at the system level. The current architecture diagram shows Software Systems Engineering upstream of Input Evaluation, while the revised system requirements describe Integration as providing report information to Input Evaluation. This allocation remains an open Gate 1 architecture item and does not change the downstream Input Evaluation → Integration → Claim Investigation flow defined above.

## 2. Definitions

- An **input report** is a bug report received by the Input Evaluation subsystem for evaluation.
- A **criterion finding** is the Input Evaluation result for one published quality criterion.
- An **identified claim** is a checkable claim recognized in an input report for downstream investigation.
- A **report context** is the information from the original report needed to interpret and investigate an identified claim.
- An **investigation request** is a record supplied by Input Evaluation to Integration for transfer to Claim Investigation.

## 3. Requirements and Verification

The IE1–IE7 headings below organize the major capabilities of the Input Evaluation subsystem. The numbered subrequirements are the individual requirements to be verified.

### IE1 — Criterion Evaluation

#### IE1.1 — Criterion Findings

**Requirement**

The Input Evaluation subsystem shall evaluate each bug report against every published quality criterion and produce exactly one finding for each criterion. Each finding shall identify the criterion ID and the version of the quality criteria used.

**Source:** R1

**Verification Method:** Test

**Draft Test:**  
Process representative bug reports and compare the resulting findings with the published quality-criterion list. Verify that every criterion appears exactly once and that every finding records the criterion ID and quality-criteria version.

---

#### IE1.2 — Finding Evidence

**Requirement**

The Input Evaluation subsystem shall cite at least one inspectable evidence item or source reference for each criterion finding and preserve the connection between the finding and the original bug report content.

**Source:** R3

**Verification Method:** Inspection / Test

**Draft Test:**  
Inspect criterion findings from representative reports and verify that each finding contains at least one evidence item or source reference that can be associated with the original report content.

---

#### IE1.3 — Unevaluated Criteria

**Requirement**

The Input Evaluation subsystem shall identify every quality criterion it could not evaluate and state the reason. When it reaches a conclusion for every criterion, it shall explicitly state that no criterion remained unevaluated.

**Source:** R4

**Verification Method:** Test

**Draft Test:**  
Process reports containing missing or ambiguous information and verify that each criterion that cannot be evaluated is identified with a reason. Process a report for which all criteria can be evaluated and verify that the output explicitly states that no criterion remained unevaluated.

---

### IE2 — Checkable Claim Identification

#### IE2.1 — Claim Identification Performance

**Requirement**

The Input Evaluation subsystem shall identify at least 80% of the checkable claims labeled in the historical evaluation.

**Source:** R7.1

**Verification Method:** Analysis / Test

**Draft Test:**  
Run claim identification on the human-labeled historical evaluation set. Compare identified claims with the reference claims using a documented matching rule and calculate claim recall.

**Acceptance Criterion:**  
Claim recall shall be at least 80%.

---

### IE3 — Claim Context and Traceability

#### IE3.1 — Claim Information Preservation

**Requirement**

The Input Evaluation subsystem shall assign each identified claim a unique identifier and preserve the exact claim text, source report reference, project identifier, relevant report context, and any project version named in the report.

**Source:** R7

**Verification Method:** Inspection / Test

**Draft Test:**  
Process reports containing multiple claims and examples with and without named project versions. Verify that every identified claim includes the required identifier, source text, report reference, project identifier, relevant context, and any project version explicitly provided in the report.

The exact uniqueness scope of the claim identifier and the required report-context fields shall be defined in the applicable subsystem interface agreement.

---

### IE4 — Integration Handoff

#### IE4.1 — Criterion Finding Handoff

**Requirement**

The Input Evaluation subsystem shall provide all criterion findings to the Integration subsystem in the agreed interface format for inclusion in the maintainer-facing output.

**Source:** R2

**Verification Method:** Test (Interface)

**Draft Test:**  
Process representative bug reports and capture the records transferred from Input Evaluation to Integration. Verify that all criterion findings are present, remain associated with the correct report, and conform to the agreed interface format.

---

#### IE4.2 — Investigation Request Handoff

**Requirement**

The Input Evaluation subsystem shall provide each investigation request and its required report context to Integration for transfer to Claim Investigation.

**Source:** R7

**Verification Method:** Test (Interface)

**Draft Test:**  
Process reports containing multiple checkable claims and verify that Integration receives an investigation request for each identified claim together with the report context required by the agreed interface contract.

---

### IE5 — Input Robustness

#### IE5.1 — Input Validation

**Requirement**

The Input Evaluation subsystem shall validate each received report against the agreed input contract and return an explicit error or unevaluated result when the input cannot be processed.

**Source:** R9

**Verification Method:** Test (Interface)

**Draft Test:**  
Submit valid, incomplete, malformed, and unsupported report inputs. Verify that valid inputs are processed and that inputs that cannot be processed return an explicit error or unevaluated result rather than an unsupported finding.

---

#### IE5.2 — Style-Variation Robustness

**Requirement**

The Input Evaluation subsystem shall produce consistent findings for semantically equivalent reports whose formatting or writing style differs, subject to the system-level threshold in R9.3.

**Source:** R9.3

**Verification Method:** Analysis / Test

**Draft Test:**  
Evaluate original reports and semantically equivalent versions with changes in formatting, grammar, or writing style while holding the criteria and model configuration constant. Compare the resulting findings using the system-defined comparison rule.

**Acceptance Criterion:**  
Agreement shall meet the R9.3 system-level threshold.

---

### IE6 — Reporter Privacy and Identity Independence

#### IE6.1 — Cross-Report Reporter Privacy

**Requirement**

The Input Evaluation subsystem shall not create or retain records that associate a reporter with more than one submission.

**Source:** R6.2

**Verification Method:** Inspection / Test

**Draft Test:**  
Process multiple reports, including multiple reports from the same contributor. Inspect outputs, stored records, logs, and relevant subsystem state and verify that no cross-submission reporter profile or association is created or retained.

---

#### IE6.2 — Identity Independence

**Requirement**

The Input Evaluation subsystem shall produce the same findings when reporter-identifying information is replaced with placeholders, subject to the system-level threshold in R6.1.

**Source:** R6.1

**Verification Method:** Analysis / Test

**Draft Test:**  
Create paired reports that differ only in reporter-identifying information. Evaluate both versions under the same criteria and model configuration and compare the resulting findings.

**Acceptance Criterion:**  
Use the current R6.1 threshold of 95% agreement while TBR-6 remains unresolved at the system level.

---

### IE7 — Evaluation Support and Provenance

#### IE7.1 — Historical Evaluation Support

**Requirement**

The Input Evaluation subsystem shall produce criterion findings in a form that can be compared with the human-labeled historical evaluation set and used to calculate system accuracy, coverage, and negative-finding correctness.

**Source:** R5

**Verification Method:** Analysis / Test

**Draft Test:**  
Run Input Evaluation on the historical evaluation set and verify that its criterion findings can be matched with the human-labeled reference results and used to calculate accuracy, coverage, and negative-finding correctness.

System-level performance thresholds remain part of system verification rather than this subsystem requirement.

---

#### IE7.2 — Output Provenance

**Requirement**

Each Input Evaluation output shall record the version of the quality criteria and every external model used to produce the findings.

**Source:** R10.3

**Verification Method:** Inspection / Test

**Draft Test:**  
Inspect representative outputs and verify that each records the quality-criteria version and the identifier or version of every external model used to produce the findings.

---

## 4. Verification Preparation

Before executing the draft verification tests, the following items should be defined or baselined:

- published quality criteria and criteria version;
- upstream input interface contract for Input Evaluation;
- Input Evaluation → Integration output interface contract;
- required report-context fields;
- human-labeled historical evaluation set;
- claim-matching rule used for claim recall;
- identity-replacement test set;
- style-variation test set;
- findings-comparison rule used for R6.1 and R9.3.

These items may remain draft or TBD at Gate 1 but should be resolved before formal verification.

## 5. Traceability Summary

| System Requirement | Input Evaluation Requirement |
|---|---|
| R1 — Quality criterion evaluation | IE1.1 |
| R2 — Output delivery support | IE4.1 |
| R3 — Evidence | IE1.2 |
| R4 — Unevaluated items | IE1.3 |
| R5 — Historical evaluation | IE7.1 |
| R6 — Reporter privacy and identity independence | IE6.1, IE6.2 |
| R7 — Checkable claims and investigation requests | IE2.1, IE3.1, IE4.2 |
| R8 — Maintainer approval | No explicit Input Evaluation allocation |
| R9 — Robustness and unusual input | IE5.1, IE5.2 |
| R10 — Reproducibility and provenance | IE7.2 |

## 6. Gate 1 Open Items

The following items remain open for subsystem and system-level coordination:

1. Confirm which subsystem owns submission classification before a report reaches Input Evaluation.
2. Confirm which subsystem owns the direct upstream interface to Input Evaluation and reconcile the architecture diagram with the revised system requirements.
3. Finalize the upstream input contract for Input Evaluation.
4. Finalize the Input Evaluation → Integration output interface contract.
5. Define the required report-context fields for investigation requests.
6. Define the uniqueness scope of claim identifiers.
7. Confirm whether Input Evaluation receives the initial issue submission or the latest available issue content.
8. Confirm the version identifiers used for published quality criteria and external models.
9. Confirm one owner from each subsystem for every active Input Evaluation interface.
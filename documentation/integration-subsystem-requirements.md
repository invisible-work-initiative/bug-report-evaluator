# Bugs26 Integration Subsystem Requirements

# Variable Legend

*Highlighted bracketed values are variables (parameters) that must be set by the team before the requirements are baselined.*

# Integration Subsystem Definition

The Integration subsystem moves information between the bug-report source, Input Evaluation, Claim Investigation, and the maintainer-facing output. It structures information for defined subsystem interfaces while preserving the original report, maintaining traceability, and exposing processing or interface failures rather than hiding them.

# Subsystem-Specific Definitions

A **supported repository** is a public GitHub repository that is within the agreed project scope and can provide issue data through the system's selected GitHub access method.

The **original report** is the issue title and body as received from the source repository before Integration structures or maps any content.

A **structured representation** is Integration's organized representation of report fields or sections for downstream use. It does not replace the original report.

A **report identifier** is the identifier used to keep a bug report associated with its derived requests, findings, evidence, and final output throughout system processing.

An **investigation request** is the claim and associated report context provided to Claim Investigation for checking against public project artifacts.

Requirements

**R1.** The system shall evaluate every incoming bug report against the quality criteria.

1. The Integration subsystem shall receive bug reports from supported GitHub repositories.  
2. The Integration subsystem shall preserve the original report and convert its content into a structured format without adding missing information.  
3. The Integration subsystem shall send the original and structured report to Input Evaluation.  
4. The Integration subsystem shall transfer investigation requests and required report context from Input Evaluation to Claim Investigation.

**R2.** The system shall deliver an output to the maintainer for each submission.

1. The Integration subsystem shall collect findings Claim Investigation.  
2. The Integration subsystem shall combine findings into the required output and send it to the maintainer-facing interface.

**R3.** Every finding shall cite the evidence that supports it.

1. The Integration subsystem shall keep each report connected to its findings, claims, and supporting evidence.  
2. The Integration subsystem shall preserve evidence source references when transferring findings.

**R6.** The system shall judge each submission independently of who filed it.

1. **R6.2** The system shall keep no record that associates a reporter with more than one submission.
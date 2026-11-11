# Automated Quality Checking of Incoming Bug Reports: Requirements
 
## Definitions
 
A **bug report** is a description of a suspected software defect submitted to an open source project's public issue tracker. Security vulnerability reports and feature requests are outside the scope of this project.
 
The **maintainer** is the person responsible for deciding what happens to a report.
 
The **quality criteria** are the properties that make a bug report usable, such as steps to reproduce, expected versus observed behavior, and accuracy of its checkable claims. The team defines and publishes the full set, drawing on published research.
 
A **checkable claim** is a statement in a report that can be confirmed or refuted using the project's public artifacts (code, version history, documentation, prior issues).
 
A **finding** is a single statement the system makes about a report, for example that a criterion is satisfied, that a claim failed verification, or that something could not be checked.
 
**Accuracy** is the proportion of a method's findings that are correct.
 
The **baseline** is a simple reference method, defined and published by the team, against which the system is compared.
 
The **historical evaluation** is a measurement of accuracy on bug reports whose outcomes are already known, drawn from at least three open source projects that differ in size and application domain.
 
## Requirements
 
R1. The system shall evaluate every incoming bug report against the quality criteria.
 
R2. The system shall present the findings for each report to the maintainer.
 
R3. Every finding shall cite the evidence that supports it, in a form the maintainer can inspect.
 
R4. Every system output shall state what the system could not check.
 
R5. The system shall be more accurate than the baseline in the historical evaluation.
 
R6. The system shall not compile information about individual people across reports.

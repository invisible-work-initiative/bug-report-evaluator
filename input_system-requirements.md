# System Requirements

## Input Evaluation Subsystem

### Definitions

- An **input report** is a bug report received by the Input Evaluation subsystem for evaluation.

- A **report context** is the information from the original bug report needed to interpret a checkable claim, such as the report title, body, repository identifier, issue URL, and surrounding text.

- An **identified claim** is a checkable claim extracted or recognized by the Input Evaluation subsystem for further investigation.

### Requirements

- **IE1.** The Input Evaluation subsystem shall evaluate every input report against the defined quality criteria.

- **IE2.** The Input Evaluation subsystem shall identify checkable claims contained in each input report.

- **IE3.** The Input Evaluation subsystem shall preserve sufficient report context for each identified claim.

- **IE4.** The Input Evaluation subsystem shall provide each identified claim and its associated report context to the Claim Investigation subsystem.

- **IE5.** The Input Evaluation subsystem shall identify any report content or quality criterion that it cannot evaluate.

- **IE6.** The Input Evaluation subsystem shall preserve the information needed to trace each identified claim back to its source in the original bug report.

- **IE7.** The Input Evaluation subsystem shall not compile information about individual people across reports.


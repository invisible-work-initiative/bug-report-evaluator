> **Draft**

# Integration Subsystem Requirements

These requirements come from the Integration items in the team's System Requirements document.

## INT-1 - Receive bug reports

**Requirement** - The Integration subsystem shall receive bug reports from supported GitHub repositories.

**Parent** - R1  
**Verification** - Test - Submit a sample GitHub bug report and check that Integration receives it.

## INT-2 - Preserve and structure reports

**Requirement** - The Integration subsystem shall preserve the original report and convert its content into a structured format without adding missing information.

**Parent** - R1  
**Verification** - Test - Compare the original report with the structured version to make sure nothing was lost or added.

## INT-3 - Send reports to Input Evaluation

**Requirement** - The Integration subsystem shall send the original and structured report to Input Evaluation.

**Parent** - R1  
**Verification** - Test - Check that Input Evaluation receives both versions of the report.

## INT-4 - Send investigation requests

**Requirement** - The Integration subsystem shall transfer investigation requests and required report context from Input Evaluation to Claim Investigation.

**Parent** - R1  
**Verification** - Test - Send a sample investigation request and check that Claim Investigation receives it with the needed context.

## INT-5 - Collect findings

**Requirement** - The Integration subsystem shall collect findings from Input Evaluation and Claim Investigation.

**Parent** - R2  
**Verification** - Test - Check that Integration receives findings from both subsystems.

## INT-6 - Send results to the maintainer

**Requirement** - The Integration subsystem shall combine findings into the required output and send it to the maintainer-facing interface.

**Parent** - R2  
**Verification** - Test - Check that the output includes the collected findings and reaches the maintainer-facing interface.

## INT-7 - Keep reports linked to their findings

**Requirement** - The Integration subsystem shall keep each report connected to its findings, claims, and supporting evidence.

**Parent** - R3  
**Verification** - Test - Check that each finding, claim, and evidence item is linked to the correct report.

## INT-8 - Preserve evidence references

**Requirement** - The Integration subsystem shall preserve evidence source references when transferring findings.

**Parent** - R3  
**Verification** - Test - Transfer a finding and check that its evidence references remain unchanged.

## INT-9 - Protect reporter privacy

**Requirement** - The system shall keep no record that associates a reporter with more than one submission.

**Parent** - R6  
**Verification** - Inspection - Check Integration's stored data and logs to make sure they do not link a reporter across submissions.

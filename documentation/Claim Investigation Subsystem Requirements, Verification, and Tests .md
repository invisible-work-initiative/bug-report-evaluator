# Claim Investigation Subsystem Requirements, Verification, and Tests

Review package: Gate 1 — Revised Draft 0.2
Subsystem: Claim Investigation
Status: Proposed for subsystem and interface-owner review
Implementation status: Requirements and tests are specified, not implemented or executed.

## 1. Purpose and Scope

The Claim Investigation subsystem evaluates checkable statements extracted from incoming bug reports by comparing those statements against publicly available project artifacts.

Its responsibilities are to validate the received claim information, determine what assertion is being made, locate relevant public project artifacts, evaluate the assertion against available evidence, and return a traceable finding or an explanation of why a finding cannot be established.

The subsystem receives claim investigation requests and associated report context from Integration. These claims and their context originate from Input Evaluation. The subsystem returns investigation results, evidence references, and feedback about invalid or ambiguous input to Integration.

The following are outside the scope of this document:

- Selection of the internal programming language, AI model, or search algorithm.

- The methods used by Input Evaluation to select checkable claims.

- The final formatting of the maintainer-facing report, which belongs to Integration.

- Final interface schemas and transport mechanisms that have not yet been approved by the relevant subsystem owners.

## 2. Terminology and Operational Definitions

Claim: A statement extracted from a bug report that asserts a property, behavior, or condition of a software project.

Claim identifier: An identifier assigned upstream that distinguishes a claim from other claims in its agreed identification scope.

Source context: Information linking a claim to its originating report and the surrounding text needed to interpret its meaning.

Project version: The release or commit used to check a claim. A report-specified version and an actually inspected version must not be confused.

Search record: An inspectable record of the repository, revision, search scope, query or method, and observed results used to support an absence finding.

Claim finding: The single conclusion associated with an identified claim, including an inconclusive conclusion and its limitations. Validation feedback is a processing response; its relationship to the system's one-finding-per-claim count requires the reconciliation described in OD-06.

Receive: Obtain a claim record through the input interface. Receipt does not imply validity or acceptance.

Validate: Check a received record against the required fields, data types, and constraints of the agreed input contract.

Accepted input: A received record that satisfies the applicable input validation rules. Acceptance does not imply that the claim is true or that sufficient evidence exists to investigate it.

Interpret: Identify the proposition to be evaluated, including the subject of the claim, the asserted behavior or property, and any relevant qualifications specified in the input.

Interpretable claim: A claim for which the subsystem can determine a sufficiently specific proposition to guide investigation without inventing missing facts.

Project artifact: A publicly accessible project resource, such as source code, documentation, version history, a commit, or an issue.

Artifact reference: Information that identifies a particular project artifact and, where necessary, its revision and relevant location within that artifact.

Evidence: An artifact or part of an artifact used to justify an investigation finding.

Supported: The identified evidence establishes the asserted proposition within the stated scope.

Contradicted: The identified evidence establishes an inconsistency with the asserted proposition within the stated scope.

Insufficient evidence: The available evidence does not establish either support or contradiction.

Unable to check: A limitation that prevents the relevant proposition from being evaluated fully. This describes the reason for an incomplete investigation, rather than independently establishing whether the original claim is true or false.

Investigation result: Information that links a claim to its evidence-based outcome, available evidence references, and applicable limitations.

Verification: The process of determining, through defined evidence and pass criteria, whether an implemented requirement has been satisfied.

JSON is currently proposed as the format for exchanging investigation results, evidence references, and limitations. The final format and its detailed structure remain subject to joint confirmation by Claim Investigation and Integration.

## 3. Inputs, Outputs, and Contract Assumptions

### 3.1 Inputs Received through Integration

Claim Investigation receives claims and associated report context through Integration. These claims and their context originate from Input Evaluation. The following input information is proposed for confirmation with Integration:

- Claim identifier

- Original claim text

- Source report identifier or URL

- Project or repository identifier

- Source context

Project version named in the report, if any

Additional context may include the report title, report body, and issue URL. Which of these items must be provided through Integration remains to be agreed with Integration.

The required and optional input fields, field types, identifier uniqueness scope, and missing-value rules remain subject to joint confirmation by Claim Investigation and Integration.

Interface boundary: Claim Investigation has no direct request, feedback, or result exchange with Input Evaluation in this draft. Integration is its sole subsystem interface. The current Claim Investigation–Integration agreement primarily specifies outgoing results; incoming requests and input feedback are proposed additions for joint agreement.

### 3.2 Outputs to Integration

The Claim Investigation–Integration interface agreement proposes the following information to be included in investigation results:

- Originating claim identifier

- Investigation outcome

- Inspectable evidence references, when available

- Explanation of limitations or inability to check

Evidence information: The outgoing agreement proposes evidence type, a reference/path/URL, and a short explanation of relevance. Final required fields remain open. Results are transferred when an investigation completes or when Claim Investigation determines that a claim cannot be fully investigated; available evidence and reasons accompany the affected claim.

The final output format, field definitions, outcome labels, and evidence representation remain subject to joint confirmation by Claim Investigation and Integration. The system requirement for exactly one finding per identified claim must be reflected in the agreed output contract. The outgoing agreement still lists one versus multiple findings as an open item; CI-SR-05 retains the system-derived one-finding rule pending reconciliation with both interface owners.

Additional proposed output information needed for system requirements: the exact original claim passage and source-report reference (R7.3); the actual release or commit checked, or an explicit inability to establish it (R7.4); and the Claim Investigation component and external-model versions used (R10.3). These additions require alignment with Integration and do not constitute an approved schema.

### 3.3 Proposed Design Assumptions

The following assumptions are introduced to make the draft requirements and tests reviewable. They are not approved interface decisions.

DA-01: The investigation can distinguish records that satisfy the input contract from records that violate it.

DA-02: The investigation can distinguish structurally valid input from input whose meaning is too ambiguous to investigate.

DA-03: Evaluation is performed against an identifiable project and, when the claim specifies a revision, the corresponding revision.

DA-04: The outcome model distinguishes evidence supporting a claim, evidence contradicting a claim, and evidence insufficient to determine it.

DA-05: Results retain enough information to associate a finding and its evidence with the originating claim.

DA-06: Integration supplies the consolidated input with enough claim/report association to distinguish the submitted claims. When an identifier is missing or invalid, the input owners must agree how feedback is correlated with the affected submission. Identifier scope, retries, and corrected requests remain to be agreed; no specific correlation field is prescribed.

DA-07: When the report does not name a version, Claim Investigation will agree a documented selection rule with Integration and confirm how the actual checked version is conveyed to Integration. Claim Investigation does not attribute that selection to the reporter.

## 4. Draft Subsystem Requirements

### CI-SR-01 — Validate incoming claim records and report failures

The Claim Investigation subsystem shall determine whether each claim record received from Integration satisfies the required-field, data-type, and format constraints jointly agreed by Integration and Claim Investigation. It shall accept conforming claim records and provide Integration with confirmation of acceptance and interpretability, or clear feedback identifying missing, invalid, or ambiguous information and the affected submission.

Verification method: Test and inspection

Pass criterion: For every test record with a known contract-conformance classification, the subsystem produces the corresponding valid or invalid determination. Conforming claim records are accepted; invalid records are identified according to the agreed handling rules. Feedback reaches Integration and identifies the affected submission and detected information problems, including when the claim identifier is unusable.

Dependency: Input contract constraints, acceptance confirmation, feedback representation, and correlation rules must be approved by Integration and Claim Investigation before final verification.

Trace: System R1 and R9. IE-CI-04, IE-CI-01, and the earlier input agreement Section 5 provide content/acceptance references pending route r evision under OD-12. The Integration-to-Claim input and Claim-to-Integration feedback contract must be documented; CI-IN-01 through CI-IN-06 do not currently define that inbound transfer.

### CI-SR-02 — Preserve claim source identity

The Claim Investigation subsystem shall maintain an association between each accepted claim and its received claim identifier, original claim text, source report reference, project identifier, and source context throughout investigation.

Verification method: Inspection and test

Pass criterion: At each tested investigation stage, the recorded associations identify the same originating claim and report as the accepted input, without mixing information from distinct claims.

Trace:  CI-IN-02; System R3, R7.3, and the Claim Investigation allocation under R7. IE-CI-02, IE-CI-03, and IE-CI-06 are upstream content-preservation references pending agreement revision. Integration delivers consolidated inputs with their original claim text, context, and associations intact; Claim Investigation preserves the received associations during investigation and output.

### CI-SR-03 — Interpret claims and identify ambiguity

For each accepted claim whose meaning can be established from the received text and context, the Claim Investigation subsystem shall identify its subject, asserted behavior or property, and input-supported qualifications. If these cannot be established, it shall identify the ambiguous or missing information without inventing an interpretation and report the limitation under CI-SR-07. It shall provide Integration with feedback identifying the information needed to interpret the claim, while conveying the investigation limitation to Integration under CI-SR-07.

Verification method: Test using independently annotated example claims

Pass criterion: The identified proposition matches the expected subject, assertion, and applicable qualifications recorded in the test oracle; the subsystem does not introduce a version, artifact, behavior, or condition unsupported by the input. Ambiguous cases identify the missing information and do not produce an unsupported definitive finding. Integration receives confirmation for interpretable claims and specific clarification feedback for ambiguous claims; the corresponding limitation is preserved in the result sent to Integration.

Design proposal: Represent the identified proposition in a reviewable form. The internal representation is not prescribed.

Trace: CI-IN-04; System R4 and R7. IE-CI-04, IE-CI-05, and earlier input agreement Section 5 provide interpretability/feedback references pending route revision. Claim Investigation sends all clarification feedback to Integration, which coordinates upstream clarification.

### CI-SR-04 — Identify public artifacts and respect the requested version

For each accepted, interpretable claim, the Claim Investigation subsystem shall seek public project artifacts relevant to the asserted proposition and record references to the artifacts used. When the received claim or report context specifies a release or commit, it shall check the claim against that version without silently substituting a different version. If relevant artifacts or the specified version cannot be obtained or established, it shall report the limitation under CI-SR-07.

Verification method: Test and inspection

Pass criterion: For test fixtures with predefined relevant artifacts, the subsystem identifies the required fixture artifacts and records references that resolve to those artifacts. Version-dependent cases use the specified revision or identify its unavailability; another revision is not presented as the requested revision.

Limit: This requirement does not prescribe a particular search technique or imply an exhaustive search of the entire public Internet.

Trace: System R3, R7, and R7.5; CI-IN-03 and CI-IN-04.

### CI-SR-05 — Return one evidence-based finding per accepted claim

For each distinct accepted claim, the Claim Investigation subsystem shall return exactly one finding reporting whether the identified evidence supports the proposition, contradicts the proposition, or is insufficient to establish either conclusion, including ambiguous and uncheckable claims. Repeated delivery of the same request shall not create additional findings.

Verification method: Test using a fixture with independently established expected outcomes

Pass criterion: For each test proposition, the reported outcome matches the fixture's expected outcome under the documented evaluation criteria. Each distinct accepted claim, including an inconclusive case, has exactly one finding without omission or duplication.

Dependency: Final outcome labels and output multiplicity require agreement with Integration. Request identity, duplicate/correction handling, and rejected-input reconciliation under R7.2 require agreement with Integration, which coordinates upstream dependencies. The outgoing agreement leaves one versus multiple findings open; exactly one finding is retained here as a system-derived requirement, not as an already approved interface decision.

Decision rule: Conflicting or partial evidence that does not establish either outcome shall produce an insufficient-evidence finding with the unresolved issue explained. Lack of accessible evidence alone shall not be treated as proof that a claim is false.

Trace: CI-IN-01 and outgoing agreement Sections 4.1 and 5.1; System R7, R7.2, and R2.1. The agreement requires results for completed investigations; the system adds completeness and duplicate-handling obligations.

### CI-SR-06 — Provide inspectable evidence and preserve its association

For each finding classified as supported or contradicted, the Claim Investigation subsystem shall provide at least one inspectable evidence reference identifying the public artifact and relevant content that justify the conclusion. Each cited link shall resolve to the intended content, and each quotation shall match its source exactly. The subsystem shall preserve the association between each finding and its own evidence, including when multiple claims share an artifact. When an investigation is inconclusive, it shall still convey any available supporting evidence and explain its limits rather than invent evidence.

Verification method: Inspection and test

Pass criterion: For every supported or contradicted fixture finding, a reviewer can resolve the cited reference to the intended artifact and relevant content; that content justifies the classification, and all quotations match the source exactly. Shared artifacts do not cause evidence to be assigned to an unrelated claim.

Design decision pending: Claim Investigation and Integration must agree the required evidence information, including the proposed evidence type, reference/path/URL, short explanation of relevance, revision identifiers, and line or symbol locations. Integration must preserve source associations while consolidating and supplying input, and Claim Investigation must retain enough incoming association to connect evidence to its originating claim.

Trace: CI-IN-03; IE-CI-06 is an upstream association reference pending route revision; System R3.1–R3.3. CI-IN-05 is Integration’s downstream preservation responsibility, supported by Claim Investigation’s supplied evidence association and verified jointly at the boundary.

### CI-SR-07 — Report limitations and dependency failures

When available information prevents an investigation from establishing a supported or contradicted outcome, the Claim Investigation subsystem shall identify the affected claim and describe the specific information or evidence limitation. When a required source or service is unavailable, or the agreed investigation time budget expires, it shall still return a finding to Integration that preserves established evidence and states the unresolved limitations. When the limitation arises from missing, invalid, or ambiguous input information, it shall also provide the relevant feedback to Integration under CI-SR-01 and CI-SR-03.

Verification method: Test and joint fault-injection test

Pass criterion: For each fixture with a known limitation, the result identifies the correct claim and the relevant limitation without asserting support or contradiction unsupported by the evidence. Failure and timeout cases return a correlated finding within the agreed budget; delivery failures follow the agreed bounded retry and failure-reporting rules.

Dependency: Integration must agree investigation time budgets, acknowledgments, transport-failure handling, and retry limits. The system 15-minute target remains end-to-end, not a separate investigation allowance.

Trace: CI-IN-04; IE-CI-05 is an upstream uncheckable-information reference pending route revision; System R4 and R9.1, with a contribution to R2.2. CI-IN-06 assigns preservation in the final output to Integration.

### CI-SR-08 — Produce contract-conforming investigation output

The Claim Investigation subsystem shall provide investigation results to Integration using the machine-readable data representation jointly agreed for the Claim Investigation–Integration interface. Each result shall preserve the received claim identifier and source-report association, a clear investigation outcome, available inspectable evidence and its relationship to the finding, and any reason the claim could not be fully checked. Results shall be provided when investigation completes or when the subsystem determines that the claim cannot be fully investigated.

Verification method: Test

Pass criterion: Every output test record conforms to the agreed output contract and can be interpreted and associated with the correct claim by Integration. Claim identifiers, outcomes, available evidence, and limitations survive transfer without changed meaning. The system-derived original claim text, actual checked version, search records where applicable, and component/model metadata are verified once their interface representation is jointly agreed. Problems accepting or associating an output are reported by Integration; they are not treated as successful delivery.

Dependency: The final machine-readable format, exact fields, outcome labels, required/optional evidence information, missing-value behavior, multiplicity, acknowledgments/error feedback, and transfer mechanism remain open under Section 8 of the outgoing agreement. Claim Investigation owns investigation content; Integration owns association and preservation, not conclusion correction or evidence creation.

Trace: CI-IN-01 through CI-IN-04; outgoing agreement Sections 4 and 5. CI-IN-05 and CI-IN-06 are Integration-owned downstream obligations supported by this output and verified jointly. System R2, R3.4, R7.3–R7.4, and R10.3.

### CI-SR-09 — Protect privacy and resist irrelevant or unsafe input

The Claim Investigation subsystem shall not create or retain records that associate a reporter with more than one submission, including in investigation outputs, intermediate data, caches, or logs. It shall base findings on the claim and project evidence rather than reporter identity, embedded instructions, or meaning-preserving style changes. If it executes submission code or commands, it shall do so in an environment with no access to system credentials.

Verification method: Inspection, paired-input tests, and conditional isolation test

Pass criterion: Inspection of outputs, intermediate data, caches, and logs from the test reports finds no retained reporter identifier or mapping that associates the same reporter with multiple submissions. Approved equivalent-input pairs preserve outcomes and substantive evidence; harmless execution probes cannot access test credential markers. If execution is unsupported, verify that restriction by inspection.

Dependency: Software Systems Engineering must clarify treatment of source-report references and reporter identifiers under R6.2. This requirement does not authorize cross-report identity retention while that boundary is unresolved.

Dependency: Software Systems Engineering must approve paired datasets and measurement rules. System-level thresholds in R6.1, R9.2, and R9.3 remain system acceptance targets.

Trace: System R6.1–R6.2 and R9.2–R9.4. These are system-derived requirements; neither supplied interface agreement defines an equivalent privacy or execution-isolation clause.

### CI-SR-10 — Record reproducibility information

The Claim Investigation subsystem shall provide Integration with its component version and the identifiers or versions of every external model used for each result, and retain a reproducible evaluation package containing fixture revisions, relevant configuration, dependencies, and run instructions.

Verification method: Inspection and repeat-run demonstration

Pass criterion: TC-15 runs from a fresh repository copy using the supplied instructions; results identify the actual component and model versions, and every metric reported by the subsystem differs by no more than two percentage points between the two documented evaluation runs.

Dependency: System-level version aggregation and full-system reproduction are jointly verified with Integration and Software Systems Engineering. If no external model is used, the result explicitly records that fact.

Trace: System R10.1–R10.3. These are system-derived requirements; the outgoing agreement does not yet define component/model version fields, which require joint alignment under OD-11.

## 5. Verification Plan

| Requirement | Verification | Proposed test coverage |
| --- | --- | --- |
| CI-SR-01 | Test and inspection | TC-01, TC-06 |
| CI-SR-02 | Inspection and test | TC-01, TC-07, TC-08, TC-11 |
| CI-SR-03 | Annotated-example test | TC-01, TC-06 |
| CI-SR-04 | Test and inspection | TC-02, TC-03, TC-05, TC-11 |
| CI-SR-05 | Outcome and completeness test | TC-02, TC-03, TC-04, TC-06, TC-11, TC-12, TC-13 |
| CI-SR-06 | Inspection and test | TC-02, TC-03, TC-07, TC-08, TC-12 |
| CI-SR-07 | Test and joint fault injection | TC-04, TC-05, TC-06, TC-08, TC-09, TC-12, TC-13 |
| CI-SR-08 | Contract test with Integration | TC-06, TC-07, TC-08, TC-09, TC-11, TC-12, TC-13, TC-15 |
| CI-SR-09 | Inspection, paired-input tests, conditional isolation test | TC-10, TC-14, TC-17 |
| CI-SR-10 | Inspection and repeat-run demonstration | TC-08, TC-15 |

System R5 and R7.6 — Joint Analysis / Test — TC-16; coordinated by Software Systems Engineering with Claim Investigation. TC-16 supports system acceptance and does not introduce an eleventh subsystem requirement.

Execution status: All test cases are planned. No implementation-test results are claimed.

The pass criteria above become executable verification criteria only after relevant interface contracts, fixtures, evaluation rules, and unresolved assumptions have been approved. For each matrix row, every applicable mapped case must meet its expected result and the Section 4 pass criterion. Pending approvals block final verification; an unsupported code-execution path still requires the inspection in TC-17.

## 6. Test Specifications

### 6.1 Proposed Controlled Fixture

Use a small, version-controlled test project containing the following function at revision v0.1:

```python
def load_timeout(config):
```

return config["timeout"]

The fixture must preserve an identifiable copy of its source files and documentation. It must also define which referenced versions, files, and measurements are unavailable.

The example is proposed fixture data, not an existing verified project artifact.

Fixture preparation: Record the source repository and immutable revision, input records, independent expected outcomes, and the reviewed input/output agreement versions. Add a second revision with changed behavior to distinguish correct-version checking from accidental use of the latest version. The fixture and expected answers remain proposed until reviewed. Prepare malformed records, independently labeled ambiguous and conflicting-evidence cases, unavailable sources and revisions, a caught internal-failure injection, a timeout, and a delivery-failure scenario. Record expected input acceptance/feedback, investigation outcome, evidence, limitations, and source associations without assuming fixed field names or serialized values.

### TC-01 — Valid input and proposition interpretation

Input: A contract-conforming claim stating that at v0.1, load_timeout accesses config["timeout"] without a default, with the complete required source metadata.

Procedure: Input Evaluation supplies the upstream information to Integration. Integration consolidates it and sends the claim record with its original report context to Claim Investigation. Evaluate contract validity and acceptance, inspect the identified proposition, and compare the claim text and context with the originating report. Inspect the same claim identifier, original text, report/project references, and source context at each tested investigation stage; observe confirmation returned to Integration.

Expected: Input passes validation; the identified subject, asserted behavior, revision, and qualifications match the annotated fixture; source identity is preserved. No subject, behavior, version, or qualification unsupported by the input is introduced. Integration’s consolidated input supplies the agreed claim characteristics and sufficient source context, and Claim Investigation confirms acceptance and interpretability.

Coverage: CI-SR-01, CI-SR-02, CI-SR-03. Content trace: IE-CI-01 through IE-CI-04, pending route revision. Verify Integration-to-Claim receipt and Claim-to-Integration confirmation; no direct Input Evaluation-to-Claim transfer is used.

### TC-02 — Evidence supports a claim

Input: A claim stating that at v0.1, load_timeout directly accesses config["timeout"].

Procedure: Evaluate the claim using the controlled source artifact and inspect the resulting classification and evidence.

Expected: Supported, with the correct claim identifier and a reference to the relevant function at the intended revision. The evidence identifies the correct artifact, revision, and relevant location; the reference resolves, any quotation matches exactly, and the cited content supports the classification.

Coverage: CI-SR-04, CI-SR-05, CI-SR-06.

### TC-03 — Evidence contradicts a claim

Input: A claim stating that at v0.1, load_timeout uses config.get("timeout", 30).

Procedure: Compare the assertion against the complete function in the controlled fixture.

Expected: Contradicted, with evidence showing direct indexing instead of the asserted default-value call. The reference resolves to the correct artifact, revision, and relevant content; any quotation matches exactly and the content justifies contradiction.

Coverage: CI-SR-04, CI-SR-05, CI-SR-06.

### TC-04 — Available evidence is insufficient

Input: A claim stating that deployment Z intermittently takes more than five seconds, with no corresponding deployment measurements in the controlled fixture. Include separate fixtures with partial evidence and conflicting evidence that do not establish either conclusion.

Procedure: Examine the available evidence and compare it with the evidence required to evaluate the timing assertion.

Expected: Insufficient evidence, with an explanation that deployment timing data is unavailable. The result must not invent timing measurements or classify the assertion as false solely because measurements are missing. Partial or conflicting evidence produces an insufficient-evidence finding with the unresolved issue explained; available evidence is retained.

Coverage: CI-SR-05, CI-SR-07.

### TC-05 — Requested artifact or revision is unavailable

Input: Separate claims referencing an unavailable project revision and a file absent from the defined repository snapshot.

Procedure: Investigate each input against the controlled artifact inventory.

Expected: The correct claim identifier is preserved. The result identifies which artifact or revision could not be established and does not claim to have examined an unavailable resource. Do not silently substitute another revision; record the actual inspected version or explicitly explain that none was checked. The unable-to-check reason reaches Integration with the affected claim.

Coverage: CI-SR-04, CI-SR-07.

### TC-06 — Invalid or ambiguous input

Input: Separate cases containing a missing required repository field, an invalid data type under the reviewed test contract, and a statement such as “It breaks there” without sufficient context. Also include a record that cannot be parsed as a claim record and a record containing several independently detectable validation failures.

Procedure: Integration supplies the consolidated input cases individually to Claim Investigation. Inspect acceptance and interpretability feedback returned to Integration, including correlation with the affected submission when its identifier is unusable. For an accepted but ambiguous claim, also inspect the finding and explanation transferred to Integration.

Expected: Missing or invalid information is identified under the agreed input validation rules, and Integration receives clear feedback and coordinates any upstream clarification. Ambiguous claims identify the missing semantic information; no unsupported definitive finding is produced. An accepted ambiguous claim still produces one inconclusive finding for Integration with the affected claim and limitation identified. No concrete serialization format, status field, or error-code catalog is assumed.

Additional TC-06 cases: missing or malformed claim identifiers, multiple invalid fields, and a structurally valid but ambiguous claim. Verify feedback with Integration using the jointly agreed submission-correlation rule. Invalid records are not silently treated as accepted; accepted ambiguous claims produce one inconclusive finding. Diagnostic feedback omits secrets, credentials, and unrelated personal data.

Coverage: CI-SR-01, CI-SR-03, CI-SR-05, CI-SR-07, CI-SR-08. Agreement coverage:  CI-IN-04 for the outgoing limitation. IE-CI-04, IE-CI-05, and the earlier input agreement Section 5 are content references pending revision to route all input feedback through Integration.

### TC-07 — Multiple claims sharing an artifact

Input: Two claims about the same function, one supported and one contradicted.

Procedure: Input Evaluation supplies both claims with their source associations. Investigate both, transfer the results and evidence to Integration, and inspect identifiers, findings, and evidence relationships across the input, investigation, and receiving stages. Integration demonstrates preservation of each supplied association without ambiguity.

Expected: Each result retains the correct originating claim identifier and evidence relationship. Reusing the same artifact does not cause results to become mixed. Inspect source associations during processing as well as the returned records, and resolve each finding’s own evidence to the content that justifies that finding. Integration preserves each result’s own evidence references and does not create missing evidence or correct a conclusion.

Additional TC-07 case: use the same local claim ID in two different reports if permitted by the agreed identifier scope. Verify that the report association prevents findings and evidence from being mixed.

Coverage: CI-SR-02, CI-SR-06, CI-SR-08; CI-IN-03, and CI-IN-05; IE-CI-06 is an upstream association reference pending route revision.

### TC-08 — Transfer results to Integration

Input: Results representing supported, contradicted, and insufficient-evidence outcomes in the jointly reviewed machine-readable representation. Include investigations that cannot be completed because of unavailable information, caught failure, or timeout, and outputs that Integration cannot accept or associate with a claim.

Procedure: Provide the results to the Integration receiver when investigation completes or is determined unable to be fully completed. Compare the transmitted and received information against the jointly agreed output contract, including original claim identifiers, source association, outcome meaning, available evidence, and reasons for limitations. Exercise both successful transfer and receiving/association failure; inspect Integration’s feedback.

Expected: Integration receives and interprets conforming results and preserves their claim identifiers, outcomes, available evidence, and limitations without changing meaning. Supported or contradicted findings have inspectable evidence justifying their classification; inconclusive findings explain the unresolved limitation and retain available evidence. Required information and missing-value handling follow the approved contract, without assuming a particular format or field naming. Integration reports outputs it cannot receive or connect to the correct claim; it does not correct conclusions or create evidence.

Additional TC-08 checks: Preserve exact claim quotations, source-report associations, actual checked versions, search records where applicable, and component/model version information once their representation has been jointly agreed to satisfy the system requirements. Check evidence references and quotations against the source and verify agreed evidence type and relevance information. Check both successful receipt and receiver rejection; producing an output alone does not establish delivery. Validation and clarification feedback is returned to Integration and tested in TC-06. Its representation and any onward upstream handling must be documented in the revised interface agreement.

Coverage: CI-SR-02, CI-SR-06, CI-SR-07, CI-SR-08, CI-SR-10; CI-IN-01 through CI-IN-05 and outgoing agreement Section 5 feedback responsibilities.

### TC-09 — Preserve uncertainty in the final output

Input: An insufficient-evidence finding and a finding whose requested revision could not be established.

Procedure: Transfer both through Integration and inspect the maintainer-facing output.

Expected: The final output preserves the applicable limitations and does not present either finding as conclusively supported or contradicted. The transmitted result preserves each limitation and any available evidence; verify CI-SR-07 and CI-SR-08 at the subsystem boundary separately from Integration’s final-presentation responsibility under CI-IN-06.

Ownership: Joint interface verification, with final presentation owned by Integration.

Coverage: CI-SR-07, CI-SR-08. Agreement coverage: CI-IN-04 and CI-IN-06.

### TC-10 — Prevent cross-report personal profiling

Input: Two test reports that contain the same fictitious author identifier.

Procedure: Process both reports and inspect investigation outputs, intermediate records, caches, and logs for reporter identifiers and mappings across submissions.

Expected: No record created or retained by Claim Investigation associates the reporter with both submissions. Inspect source-reference handling against the agreed R6.2 interpretation; do not claim a pass while that interpretation remains unresolved.

Dependency: Final verification design requires clarification of the system R6 allocation and permitted data retention.

Coverage: CI-SR-09.

### TC-11 — Finding completeness, source text, and version

Input: An approved batch of distinct claims covering supported, contradicted, ambiguous, and unavailable-evidence cases; include an explicit older revision, a report without a version, and a repeated request.

Procedure: Integration submits the consolidated batch to Claim Investigation; observe resulting findings at Integration. Compare accepted claim identities with findings, compare quotations with source passages, and inspect the actual evidence revision. For the no-version case, apply the jointly documented selection rule. Deliver the identical input request more than once under the agreed request identity and observe internal result records and the final receiver state.

Expected: Exactly one finding per distinct accepted claim; no duplicate from the retry; exact quotations and correct source associations; the specified version is respected and the actual checked version is recorded. Rejected requests remain accounted for under the agreed system reconciliation rule. No accepted claim is omitted, including ambiguous and uncheckable cases. For the no-version case, the selected revision is not presented as a version supplied by the reporter.

Coverage: CI-SR-02, CI-SR-04, CI-SR-05, CI-SR-08; System R7.2–R7.5. Agreement coverage: CI-IN-01 and CI-IN-02; exactly one final finding remains system-derived pending OD-06 reconciliation.

### TC-12 — Evidence fidelity and absence findings

Input: A fixture claim asserting that a named symbol exists in a fully inspectable revision, where the controlled inventory establishes that it does not; a second case makes the repository inaccessible. Include evidence references and quotations with independently known source content.

Procedure: Inspect search scope and results, reproduce the absence search, resolve references, and compare quotations exactly with source text.

Expected: The absence-based contradiction includes a search record supporting its scope; the inaccessible case returns a limitation rather than an absence claim. Links and quotations match the actual sources. The search record identifies repository, revision, search scope, query or method, and observed results. The inaccessible-source case explains source unavailability and does not fabricate search evidence. Search-record detail derives from the system requirement and requires agreement on its output representation.

Coverage: CI-SR-05, CI-SR-06, CI-SR-07, CI-SR-08; System R3.1–R3.4 and R4.

### TC-13 — Dependency failure and timeout

Input: Valid requests with injected repository failure, external-service failure, and an investigation exceeding the jointly agreed time budget. Include a caught internal failure after evidence has been collected, a timeout after partial evidence, and a separate transport-delivery failure.

Procedure: Observe completion time and the result received by Integration, including the claim association, evidence obtained before failure, and limitation. Measure the agreed investigation budget and bounded retry count; compare evidence before the interruption with evidence in the returned finding.

Expected: A correlated result reaches the receiver within the agreed budget and identifies the failure or timeout. If delivery itself fails, the agreed bounded retry and failure-reporting behavior is observed. Each distinct accepted claim still has one finding. Caught internal failure, timeout, or unavailable sources produce an inconclusive finding with the specific unresolved limitation and all evidence already obtained. Preserve claim association and never label a failed delivery as successful; acknowledgment and transport behavior require joint agreement.

Dependency: Timing budget and transport-failure rules require joint approval before execution. The system 15-minute target is end-to-end; it is not an additional investigation allowance.

Coverage: CI-SR-05, CI-SR-07, CI-SR-08; System R9.1 and contribution to R2.2.

### TC-14 — Identity, manipulation, and style variations

Input: Independently reviewed pairs with the same underlying claim and project evidence: reporter identifiers replaced with placeholders; irrelevant instructions added to report text; and semantically equivalent writing-style variants.

Procedure: Hold project revision, configuration, and model version constant and compare outcomes and substantive evidence across each pair.

Expected: Each controlled pair has the same outcome and substantive evidence basis; source quotations faithfully reflect their respective input. Record agreement rates for the larger system datasets against the 95% targets in R6.1 (TBR-6), R9.2, and R9.3 without treating a small fixture as proof of system performance.

Coverage: CI-SR-09; System R6.1 and R9.2–R9.3; joint evaluation allocation remains subject to Software Systems Engineering review.

### TC-15 — Fresh-copy reproduction and version metadata

Input: A fresh repository checkout, documented dependencies and configuration, pinned fixtures, and an approved evaluation dataset.

Procedure: Follow only the repository instructions, run the evaluation twice, and inspect result metadata and reported metrics.

Expected: Both runs complete; component and model versions are recorded accurately; reported subsystem metrics differ by no more than two percentage points. Record inability to pin an external model version as an unresolved reproducibility limitation. Inspect the retained evaluation package for fixture revisions, relevant configuration, dependencies, and run instructions. Every result records the actual component version and every external model identifier/version, or explicitly records that no external model was used; the output representation remains to be agreed.

Coverage: CI-SR-08, CI-SR-10; System R10.1–R10.3, with complete system verification performed jointly.

### TC-16 — Historical and fabricated-claim evaluation

Input: Approved human-labeled historical and fabricated-claim datasets, a defined baseline, frozen scoring rules, and reproducible run configuration.

Procedure: Compare findings against the labels and report accuracy, coverage, negative-finding correctness, and the fraction of altered claims correctly refuted. Retain per-claim results for system aggregation.

Expected system criteria: R5.1 requires the 95% confidence interval for the accuracy difference over baseline to lie entirely above zero; R5.2 requires coverage of at least 80%; R5.3 requires negative-finding correctness of at least 90% (TBR-5); R7.6 requires refutation of at least 80% of altered claims.

Ownership: Software Systems Engineering coordinates system scoring and acceptance. Claim Investigation supplies its findings and evidence; these system targets are not silently assigned as separate subsystem targets. Dataset composition, metric denominators, confidence-interval method, and subsystem allocation require approval. TC-16 uses the outcomes, evidence, and reproducibility records produced under CI-SR-05, CI-SR-06, and CI-SR-10; passing their fixture tests alone does not demonstrate R5 or R7.6 acceptance.

Coverage: Joint system evaluation of R5 and R7.6; supporting subsystem outputs from CI-SR-05, CI-SR-06, and CI-SR-10. This is not a separate subsystem acceptance target.

### TC-17 — Conditional isolation of executed submission content

Input: Harmless probe code supplied as report content, with test-only credential markers outside the execution environment.

Procedure: If submission code execution is supported, inspect isolation configuration and attempt access through environment variables, filesystem mounts, and host credential endpoints.

Expected: No test credential marker is accessible. If execution is unsupported, inspect the relevant paths to confirm report code remains data and record the execution test as not applicable. The inspection branch must pass even when the execution probe is not applicable; unsupported execution does not waive CI-SR-09.

Coverage: CI-SR-09; System R9.4.

## 7.  System and Interface Traceability

The system requirements currently identify:

● R1: Evaluate incoming bug reports against quality criteria. Bug-report quality evaluation is upstream; CI-SR-01 validates the received claim record and does not replace that system responsibility.

● R2: Present findings to the maintainer. CI-SR-05 supplies findings; CI-SR-08 supplies contract-conforming outputs. CI-SR-07 contributes failure/timing behavior to R2.2. Final presentation remains owned by Integration.

● R3: Cite inspectable evidence for findings. CI-SR-02 preserves source identity, CI-SR-04 locates artifacts, CI-SR-06 governs inspectable evidence and its association, and CI-SR-08 enforces the search-record rules under R3.4.

● R4: State what could not be checked. CI-SR-03 identifies ambiguity and CI-SR-07 reports limitations; CI-SR-08 carries them in the agreed response.

● R5: Demonstrate higher historical-evaluation accuracy than the baseline. TC-16 remains a joint system evaluation; no quantitative subsystem target has been added to the ten CI-SR requirements.

R6: Preserve findings under reporter-identity substitution and retain no record associating a reporter with multiple submissions. CI-SR-09 covers R6.1–R6.2 through TC-10 and TC-14, subject to the agreed privacy boundary and system evaluation rules.

R7: Check every identified checkable claim against public project artifacts, with one finding per claim, its source quotation, and the checked version. CI-SR-02 and CI-SR-08 preserve source text and association; CI-SR-03 interprets claims; CI-SR-04 respects the requested version; CI-SR-05 ensures one finding per accepted claim. CI-SR-08 records the actual checked version. R7.1 remains upstream and R7.6 is evaluated jointly in TC-16.

R8 (proposed): Change submission state only with maintainer approval. Claim Investigation does not perform maintainer-facing state changes in the current scope.

R9: Tolerate unavailable dependencies and adversarial or unusual input; isolate any execution of submission content. CI-SR-01 validates malformed input, CI-SR-07 covers dependency failure and timeout under R9.1, and CI-SR-09 covers identity/style manipulation and conditional execution isolation under R9.2–R9.4.

R10: Enable reproduction from the public repository and record the versions used to produce results. CI-SR-10 covers R10.1–R10.3; CI-SR-08 also carries component/model version metadata under R10.3. TC-15 verifies subsystem reproduction; full-system reproduction remains joint.

The current allocation is CI-SR-01 through CI-SR-10 in Section 4. Section 5 maps each requirement to its planned tests, and Section 6 identifies the current coverage for every test. System-level responsibilities and approval conditions remain as stated below.

R5 requires additional coordination: The system-level accuracy and baseline requirement is not yet assigned a quantitative subsystem-specific performance target in this draft. The Software Systems Engineering team and Claim Investigation must determine how investigation accuracy contributes to the integrated historical evaluation.

Allocation boundary: Claim extraction and its R7.1 identification target belong to Input Evaluation. Input Evaluation supplies information to Integration, which consolidates and sends it to Claim Investigation. Claim Investigation returns input feedback and findings to Integration. Integration coordinates upstream clarification and owns connecting and preserving supplied results and final presentation. R4.3 requires system-level confirmation when nothing remains unchecked, so all three subsystems must agree how received, rejected, and investigated claims are reconciled through Integration. System performance targets are jointly verified, not automatically allocated in full to this subsystem.

The supplied references are Input Evaluation–Claim Investigation, Draft 0.1 dated September 25, 2026 (IE-CI-01 through IE-CI-06), and Claim Investigation–Integration, with Proposed Draft 0.2 changes dated October 18, 2026 (CI-IN-01 through CI-IN-06; the six requirements remain unchanged from Draft 0.1). Neither agreement has been approved by both owners. This requirements revision follows the clarified architecture: Claim Investigation receives only Integration-consolidated input and communicates through Integration. The earlier direct Input Evaluation–Claim route must be revised; the existing CI-IN result clauses do not establish the inbound transfer contract. The crosswalk records content traceability and outstanding agreement changes, rather than claiming full agreement consistency.

### 7.1 Agreement Coverage and Verification Ownership

IE means Input Evaluation; CI means Claim Investigation; IN means Integration. IE-CI-01–06 remain references for upstream content and acceptance behavior, with their interface route and ownership pending revision. Planned Claim-boundary tests use IN and CI; end-to-end provenance checks include IE upstream. CI-IN-05–06 remain Integration obligations. CI-SR references identify supporting behavior without transferring another subsystem’s obligations to CI. The planned owners below are for the clarified architecture, not a claim that the draft agreements have already been amended.

| Agreement ID | CI-SR support | Responsibility and boundary | Planned method and owner | Tests |
| --- | --- | --- | --- | --- |
| IE-CI-01 | CI-SR-01 | IE content reaches CI through IN consolidation; CI validates it. Direct-route clause needs revision. | Test; planned IN + CI; IE upstream | TC-01 |
| IE-CI-02 | CI-SR-02 | IN supplies consolidated report context; CI preserves original associations. Route revision pending. | Inspection / Test; planned IN + CI; IE upstream | TC-01, TC-07 |
| IE-CI-03 | CI-SR-02 | Original IE text/context must survive IN consolidation and CI receipt. Route revision pending. | Inspection; planned IE + IN + CI | TC-01, TC-11 |
| IE-CI-04 | CI-SR-01, CI-SR-03 | CI accepts conforming IN-supplied input and confirms interpretability to IN. Input contract pending. | Test; CI with IN | TC-01, TC-06 |
| IE-CI-05 | CI-SR-03, CI-SR-07 | CI identifies uncheckable input and returns feedback to IN for upstream coordination. Route revision pending. | Test; planned IN + CI | TC-06 |
| IE-CI-06 | CI-SR-02, CI-SR-06 | Preserve claim/source links from IE through IN to CI and evidence. Route revision pending. | Demonstration / Test; planned IE + IN + CI | TC-07 |
| CI-IN-01 | CI-SR-05, CI-SR-08 | CI supplies a result for each completed investigation; IN receives it. | Test; CI + IN | TC-08, TC-11 |
| CI-IN-02 | CI-SR-02, CI-SR-08 | CI preserves the incoming claim identifier through output; both verify it survives receipt. | Inspection / Test; CI + IN | TC-08, TC-11 |
| CI-IN-03 | CI-SR-06, CI-SR-08 | CI supplies inspectable evidence when available and its relationship to the finding. | Inspection; both output owners | TC-07, TC-08, TC-12 |
| CI-IN-04 | CI-SR-03, CI-SR-07, CI-SR-08 | CI identifies the affected claim and transfers the unable-to-check reason to IN. | Test; CI + IN | TC-06, TC-08, TC-09, TC-13 |
| CI-IN-05 | CI-SR-06, CI-SR-08 | IN preserves supplied result/evidence associations; CI supplies them and supports verification. | Demonstration / Test; IN | TC-07, TC-08 |
| CI-IN-06 | CI-SR-07, CI-SR-08 | IN preserves uncertainty in the final report; CI supplies the limitation and supports verification. | Test; CI + IN | TC-09 |

Agreement sections without numbered clauses: The earlier input agreement Sections 4–5 inform content and feedback requirements in CI-SR-01–03 and TC-01/TC-06, but their direct route must be revised. Output agreement Sections 4–5 support evidence type/relevance proposals, transfer triggers, receiving feedback, and the content/preservation boundary in CI-SR-06–08 and TC-07–09. Integration-to-Claim consolidated input, Claim-to-Integration input feedback, and onward upstream handling require explicit documentation under OD-01, OD-03, and OD-12. Section 8 open items remain dependencies below. CI-SR-09 and CI-SR-10 derive from system requirements and are not new agreement clauses.

## 8. Open Design Decisions

### OD-01 — Input contract: Agree consolidated incoming fields, types, identifier scope, feedback correlation, reported-version information, and validation constraints with Integration. Integration coordinates upstream clarification of the earlier input draft’s Section 4.2 required-context list and Section 8 open items. Document Integration-to-Claim transfer without inventing an existing agreement clause. Related requirements: CI-SR-01 and CI-SR-02; IE-CI-01 through IE-CI-04 as content references pending route revision.

### OD-02 — Interpretability: Define annotated examples and the minimum input-supported subject, assertion, and qualifications. Agree with Integration how missing or ambiguous information and compound claims needing upstream clarification are handled, including any impact on finding counts. Claim Investigation shall not silently split a claim into additional findings. Related requirements: CI-SR-03 and CI-SR-05; IE-CI-04 and IE-CI-05.

### OD-03 — Input feedback: Integration and Claim Investigation must agree acceptance/interpretability confirmation, missing/invalid/ambiguous-information feedback, unusable claim identifiers, and correlation with submissions. Claim Investigation sends this feedback to Integration; Integration coordinates upstream requests and returns corrected consolidated input. Distinguish input acceptance feedback from investigation outcomes, although both are sent to Integration. Related requirements: CI-SR-01, CI-SR-03, and CI-SR-07; earlier input agreement Section 5 and IE-CI-05 require route revision.

### OD-04 — Evidence references: Agree artifact types, reference granularity, search records, and inaccessible-source handling. Resolve with Integration and Software Systems Engineering how R3.1's evidence requirement applies to inconclusive findings; never invent evidence to fill a field. Related requirements: CI-SR-04, CI-SR-06, and CI-SR-08. Confirm the outgoing agreement’s proposed evidence type, reference/path/URL, and short relevance explanation. Preserve upstream source association through Integration, retaining IE-CI-06 as a content reference pending route revision, and CI-IN-03 evidence provision; Integration owns downstream preservation under CI-IN-05.

### OD-05 — Investigation outcomes: Confirm the final outcome labels with Integration and distinguish investigation conclusions from input acceptance and inability-to-check reasons. Agree how conflicting or partial evidence is explained. Outcome meaning is retained without prescribing serialized values. Related requirements: CI-SR-05, CI-SR-07, and CI-SR-08; CI-IN-01 and CI-IN-04.

### OD-06 — Output contract and multiplicity: Reconcile the outgoing agreement’s open one-versus-multiple-findings question with System R7.2 and CI-SR-05. With Integration coordinating upstream input dependencies, define distinct claims, repeated and corrected inputs, rejected-input accounting, completion indication, and replacement without duplicate final findings. With Integration, agree the machine-readable format, exact fields, evidence representation, missing values, acknowledgments/error feedback, and transfer mechanism. Confirm the system-derived original text, checked version, search record, and metadata information. Related requirements: CI-SR-02, CI-SR-04, CI-SR-05, and CI-SR-08; CI-IN-01 through CI-IN-04.

### OD-07 — Evaluation allocation: Agree historical and fabricated-claim datasets, independent labels, baseline comparison, metric definitions, and Claim Investigation's contribution to R5 and R7.6 with Software Systems Engineering. Related requirements: CI-SR-05, CI-SR-06, and CI-SR-10 as supporting outputs; TC-16 remains joint system evaluation.

### OD-08 — Privacy and robustness: Clarify R6.2 treatment of source references and intermediate data, and approve identity-substitution, manipulation, and style-variation datasets and allocations under R6.1 and R9.2–R9.3. Related requirements: CI-SR-09.

### OD-09 — Evidence of completed verification: Define how executed tests, artifacts, versions, and observed results will be recorded during later implementation gates. Related requirements: CI-SR-01 through CI-SR-10. For each run, record the test ID, current CI-SR coverage, fixture and software/model versions, inputs, expected and observed results, evidence locations, pass/fail or blocked status, and reviewer. Unexecuted tests remain planned.

### OD-10 — Failure and timing: Agree investigation time budgets, timeout reporting, delivery acknowledgments, bounded retries, and receiving/association feedback with Integration to support R2.2 and R9.1. Describe failures and limitations without a fixed error-code catalog. Allocate the investigation budget within the end-to-end target and distinguish producing a result from successful delivery. Input-interface delivery, feedback, and correction behavior must also be agreed with Integration, which coordinates upstream handling. Related requirements: CI-SR-01, CI-SR-07, and CI-SR-08.

### OD-11 — Reproducibility: Agree version metadata, configuration capture, dependency pinning, and system-level aggregation with Integration and Software Systems Engineering. Decide whether submission-code execution is in scope; if so, approve isolation controls under R9.4. Related requirements: CI-SR-10 and CI-SR-09.

### OD-12 — Agreement route revision and approval: Revise the earlier Input Evaluation–Claim draft so it no longer implies a direct operational interface. Document Input Evaluation-to-Integration upstream delivery, Integration-to-Claim consolidated input, and Claim-to-Integration acceptance/clarification feedback, including Integration’s upstream coordination responsibilities. Update the Claim–Integration agreement to cover inbound input and feedback as well as its existing outgoing result obligations; retain clause identifiers as references until the owners assign any revised identifiers. Update Related Documents accordingly and obtain affected owners’ approval. Reconcile context and missing-value open items, output multiplicity, and system-derived output information. Concrete formats, field names, status values, and error codes remain undecided and are not specified here. Section 7.1 records proposed traceability, not amended agreements or completed verification.

## 9. Revision Status

This draft organizes input validity, proposition interpretation, artifact identification, outcome classification, evidence traceability, limitation reporting, and output transfer into ten independently reviewable subsystem requirements, also covering privacy, input safety, and reproducibility. Sections 5–8 use the current CI-SR-01 through CI-SR-10 allocation.

It is not an approved interface specification or proof of completed software verification. All proposed changes require review by the Claim Investigation team, with relevant boundary decisions confirmed by the adjacent subsystem owners.

Revision note — October 19, 2026: Corrected the interface route following architecture clarification. Claim Investigation receives Integration-consolidated input and returns all input feedback and investigation results to Integration; it does not directly interface with Input Evaluation. The ten CI-SR requirements are retained, with local edits to interface wording, verification, tests, traceability, and open decisions. All twelve supplied agreement clauses remain mapped, with the earlier direct-input route explicitly marked for agreement revision. Concrete response-format and error-code prescriptions remain absent. This clean copy removes superseded wording and review formatting. Both agreements and all tests remain unapproved/planned as applicable; no implementation or executed result is claimed.

**System Requirements** 

**R1.** The system shall evaluate every incoming bug report against the quality criteria.

* **R1.1** The system shall produce exactly one finding for each quality criterion for each bug report.  
* **R1.2** Each criterion finding shall identify its criterion by ID and by the version of the published quality criteria.

**R2.** The system shall deliver an output to the maintainer for each submission.

* **R2.1** The output for a bug report shall contain every finding the system produced for that report.  
* **R2.2** The system shall deliver the output for at least 95% of submissions within 15 minutes of receiving them.

**R3.** Every finding shall cite the evidence that supports it.

* **R3.1** Every evidence item shall match its source: each link resolves to the cited content, and each quotation matches the source text exactly.  
* **R3.2** A finding that refutes a claim because something does not exist shall cite a search record.

**R4.** Every system output shall state what the system could not check.

* **R4.1** The output shall list every finding with the status of either  *supported, unsupported, partially supported* or *unable to assess*  
* **R4.2** Each item listed under R4.1 shall state why the system could not reach a conclusion.  
* **R4.3** When the system reaches a conclusion on every criterion and claim, the output shall say so.

**R5.** The system shall be more accurate than the baseline in the historical evaluation

* **R5.1** The system's accuracy shall exceed the baseline's, with the 95% confidence interval of the difference lying entirely above zero.  
* **R5.2** The system's coverage shall be at least 80%.  
* **R5.3** At least 90% (TBR-5) of the system's negative findings shall be correct.

**R6.** The system shall judge each submission independently of who filed it.

**R7.** The system shall check each checkable claim in a bug report against the project's public artifacts.

* **R7.1** The system shall identify at least 80% of the checkable claims labeled in the historical evaluation.  
* **R7.2** The system shall produce exactly one finding for each claim it identifies.  
* **R7.3** Each claim finding shall quote the passage of the report that contains the claim.  
* **R7.4** Each claim finding shall identify the project version (release or commit) against which the claim was checked.  
* **R7.5** When a report names a project version, the system shall check the report's claims against that version.  
* **R7.6** The system shall refute at least 80% of the altered claims in the fabricated-claim test set.

**R8.** The system shall tolerate failed dependencies and adversarial or unusual input.

* **R8.1** When a source the system depends on is unavailable, the system shall still deliver an output for the submission.  
* **R8.2** If the system runs code or commands taken from a submission, it shall run them in an environment with no access to the system's credentials.

**R9.** The system's results shall be reproducible from the public repository.

* **R9.1** The system and the historical evaluation shall run from a fresh copy of the repository using only the instructions in it.  
* **R9.2** Two runs of the historical evaluation shall produce each reported metric within 2 percentage points of each other.  
* **R9.3** Each output shall record the versions of the system, of the quality criteria, and of every external model used to produce it.

**R9.** The system shall be accompanied with guidelines/instructions on how to best use it and how to interpret the outputs 
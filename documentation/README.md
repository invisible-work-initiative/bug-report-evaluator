# Where to put documents

Put the file in the place below and open a pull request. It is official once it is on `main` and a teammate has approved it. Until then, write `Draft` at the top. Other subsystems can read a draft. They build to the merged document.

| Document | Where it goes |
|---|---|
| System requirements | [system-requirements.md](system-requirements.md) |
| Concept of operations | `conops.md` in this folder |
| System tests and the baseline | `system-verification.md` in this folder |
| A subsystem's requirements, tests, or working agreement | That subsystem's folder below |
| An interface agreement | [interfaces](interfaces/) |
| A decision worth remembering | [decisions](../decisions/) |
| A weekly update | Slack `#bugs26` |

| Subsystem | Folder |
|---|---|
| Software Systems | [software-systems](subsystems/software-systems/) |
| Input Evaluation | [input-evaluation](subsystems/input-evaluation/) |
| Claim Investigation | [claim-investigation](subsystems/claim-investigation/) |
| Integration | [integration](subsystems/integration/) |

Name an interface file after the two subsystems, for example `input-evaluation-integration.md`. Both owners approve that pull request. The process is on the [interface page](interface-agreements.md).

This map is [decision 0001](../decisions/0001-repository-document-organization.md).

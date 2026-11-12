# Interface list

Integration keeps this list, as described in [interface management](management.md). Last checked 2026-11-11 against the remote branches. An empty cell means no direct interaction.

## N² diagram

Read across: the row provides the cell content to the column.

| from \ to | Integration | Input Evaluation | Claim Investigation | Software Systems | GitHub | Maintainer |
|---|---|---|---|---|---|---|
| **Integration** | Integration | Original and structured report | Claim and context | Maintainer output (assumed; format not agreed) | Issue fetch request | Result page |
| **Input Evaluation** | Ratings, claims, errors | Input Evaluation | | | | |
| **Claim Investigation** | Finding per claim | | Claim Investigation | | Repository reads (our assumption) | |
| **Software Systems** | Historical test reports (assumed; to confirm) | | | Software Systems | | |
| **GitHub** | Issue content | | | | GitHub | |
| **Maintainer** | Issue URL, paste, upload | | | | | Maintainer |

## Interfaces

| Interface | Agreement | Owners | Status | Missing |
|---|---|---|---|---|
| Input Evaluation - Integration | IE v1: `documentation/Interface Agreemtn/input-evaluation-integration.md` on `origin/Input-evaluation`. Our draft: [input-evaluation-integration.md](input-evaluation-integration.md) | Integration: Meshaal Aldawood. IE: Julian or Lurui (one to be named) | Two drafts, neither approved | One agreed file here; IE answers on decision, paste and upload, snapshots; transport (IE target 2026-11-24) |
| Claim Investigation - Integration | `documentation/claim_investigation_interface_agreement.md` on `origin/claim-investigation`. Our draft: [claim-investigation-integration.md](claim-investigation-integration.md) | Integration: Meshaal Aldawood. CI: Boyu or Qinyue (one to be named) | Two drafts, neither approved | One agreed file here; final outcome strings, input record, one call per claim or per report, transport |
| Integration - Software Systems | None | Not named | **MISSING** | Whole agreement: maintainer output format and system tests |
| Integration - Maintainer | None needed. External user of the web page | Not applicable | Not applicable | INT-6 sets what the output must contain |
| Integration - GitHub | None needed. External service | Not applicable | Not applicable | INT-1 sets which repositories are supported ([decision 0004](../decisions/0004-supported-repositories-list.md)) |

## Notes

- The IE and CI agreements still sit on their own branches under other file names. Each takes effect when both owners approve a pull request that adds it here.
- Software Systems has no direct interface with IE or CI in this diagram. If that is wrong, the owners should say so.

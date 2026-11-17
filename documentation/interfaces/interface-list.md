# Interface list

Integration keeps this list, as described in [interface management](management.md). Last checked 2026-11-11 against the remote branches. An empty cell means no interface.

## N² diagram

Interfaces are code exchanged between three subsystems: Integration, Input Evaluation and Claim Investigation. Read across: the row provides the cell content to the column.

| from \ to | Integration | Input Evaluation | Claim Investigation |
|---|---|---|---|
| **Integration** | Integration | Original and structured report | Claim and context |
| **Input Evaluation** | Ratings, claims, errors | Input Evaluation | |
| **Claim Investigation** | Finding per claim | | Claim Investigation |

## Interfaces

| Interface | Agreement | Owners | Status | Missing |
|---|---|---|---|---|
| Input Evaluation - Integration | IE v1: `documentation/Interface Agreemtn/input-evaluation-integration.md` on `origin/Input-evaluation`. Our draft: [input-evaluation-integration.md](input-evaluation-integration.md) | Integration: Meshaal Aldawood. IE: Julian or Lurui (one to be named) | Two drafts, neither approved | One agreed file here; IE answers on decision, paste and upload, snapshots; transport (IE target 2026-11-24) |
| Claim Investigation - Integration | `documentation/claim_investigation_interface_agreement.md` on `origin/claim-investigation`. Our draft: [claim-investigation-integration.md](claim-investigation-integration.md) | Integration: Meshaal Aldawood. CI: Boyu or Qinyue (one to be named) | Two drafts, neither approved | One agreed file here; final outcome strings, input record, one call per claim or per report, transport |

## Notes

- The IE and CI agreements still sit on their own branches under other file names. Each takes effect when both owners approve a pull request that adds it here.
- Software Systems has no interface. Its work is requirements, tests and evaluation data.

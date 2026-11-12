# 0007: The snapshot is kept for the run and returned in the output

**Date:** 2026-11-11
**Status:** proposed
**Deciders:** Integration subsystem (Meshaal Aldawood); accepted when the pull request is approved

## Context

IE's draft (section 4.3) says Integration keeps each snapshot, so that evidence line numbers can be resolved later. Our requirement INT-9 says the system keeps no record that links a reporter to more than one submission, and the prototype stores nothing. We have asked IE whether it needs a snapshot kept after the run. We have no answer yet. IE's transport decision is due 2026-11-24.

## Decision

The snapshot is the `IEReportRecord` sent to IE: the exact title and body, the sections and their line numbers, and the `request_id` and `snapshot_id`. Integration keeps it in memory for the length of the run and puts it in the maintainer output as `record`. The downloadable JSON contains it, so the lines IE cites can be resolved from the output alone. Integration keeps no persistent store until IE says one is needed.

## Alternatives we considered

Writing snapshots to a database. It would meet IE's wording at once, but it creates stored data that needs inspection under INT-9, and nobody has asked for it yet.

Keeping only the hash. The line numbers in IE's evidence could not be resolved from a hash.

## Consequences

Nothing outlives the request, so INT-9 is unaffected: the record has no reporter field and no key that links submissions. If IE needs retention across runs, we add a store and revisit this record and the INT-9 inspection checklist. A maintainer who loses the downloaded JSON loses the snapshot; the GitHub issue is still the source.

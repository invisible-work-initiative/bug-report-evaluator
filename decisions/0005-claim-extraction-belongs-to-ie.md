# 0005: Claim extraction belongs to IE

**Date:** 2026-11-11
**Status:** proposed
**Deciders:** Integration subsystem (Meshaal Aldawood); accepted when the pull request is approved

## Context

The first prototype pulled code references out of the report text inside Integration and built the requests for Claim Investigation from them. IE's draft says IE identifies claims and returns them as `identified_claims`. INT-2 only asks Integration to structure the report without adding missing information.

## Decision

Integration structures sections only. It splits the report at headings, keeps the raw text, and records what it could not recognize as diagnostics. IE identifies claims. The prototype no longer extracts code references in Integration. Until IE's implementation exists, a placeholder IE stub does it for demos, and that stub is not part of Integration.

## Alternatives we considered

Keeping extraction in Integration. It duplicates IE's job and could disagree with it. It also puts the judgment of what counts as a checkable claim in the wrong subsystem.

## Consequences

Integration is simpler and closer to INT-2. The demo depends on the IE stub until IE delivers. Unrecognized headings are not reported to the maintainer as gaps, because IE reads the raw text. They go only to extraction diagnostics.

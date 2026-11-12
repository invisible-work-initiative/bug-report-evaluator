# 0003: Routing follows IE's identified claims

**Date:** 2026-11-11
**Status:** proposed
**Deciders:** Integration subsystem (Meshaal Aldawood); accepted when the pull request is approved

## Context

Our SYSEN 5100 design work (BRE-DR.11) had Input Evaluation return a decision: investigate, request more information, or do not investigate. Integration called Claim Investigation only on "investigate". IE's v1 interface has no such decision. It returns ratings, `identified_claims`, and a `claim_extraction` status. IE's draft says "Integration forwards every ... claim it receives", and that a low-quality report can still contain checkable claims. We have asked IE whether it wants an overall decision and have no answer yet.

## Decision

Integration sends every claim in `identified_claims` to Claim Investigation, one call per claim. It skips only with a stated reason, which goes to the maintainer as a "could not check" item. The reasons are: `no_checkable_claims` is true, `claim_extraction` is `not_performed`, or `processing_status` is `invalid_input` or `failed`. This replaces the BRE-DR.11 rule, and the decision logic is deleted.

## Alternatives we considered

Keeping the three-way decision. IE does not produce it, so Integration would have to invent it, and judging report quality belongs to IE.

Calling CI once per report with all claims. CI's requirements hint at a batch, but its agreement is not settled. One call per claim matches IE's per-claim records. This is an open question to CI.

## Consequences

Routing is mechanical and has no judgment in it. A poor report still gets its claims checked. If IE later adds a decision, we revisit this record. The design work's rule no longer matches the code, so the design documents need a note.

# 0002: Subsystem calls are in-process for the alpha

**Date:** 2026-11-11
**Status:** proposed
**Deciders:** Integration subsystem (Meshaal Aldawood); accepted when the pull request is approved

## Context

Integration has to call Input Evaluation (IE) and Claim Investigation (CI). Neither team has chosen a transport. IE's draft sets a decision date of 2026-11-24. The CI interface agreement leaves transport and timeouts open, and CI has no decision date. Both teams say the content of the records does not depend on the transport.

## Decision

For the alpha, Integration calls IE and CI as Python function calls. Each call goes through a `typing.Protocol` interface, so the real subsystem or a stub can sit behind it. This is provisional. It waits for IE's decision on 2026-11-24 and for a CI decision that does not exist yet. We invent no timeout number.

## Alternatives we considered

An HTTP service for each subsystem. It may be the final answer, but no team has chosen it, and building it now would guess at an agreement that is not written.

Message files passed between processes. It has the same problem and adds file handling we do not need for a demo.

## Consequences

The prototype runs as one process, and swapping in a real IE or CI means writing a class that fits the Protocol. If either team picks a different transport, only the adapter behind the Protocol changes. Our interface drafts say "function call (provisional)". Revisit this record after 2026-11-24.

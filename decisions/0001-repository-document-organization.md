# 0001: Where documents go

**Date:** 2026-10-27
**Status:** proposed
**Deciders:** Integration subsystem. Accepted when this pull request is approved.

## Context

Files had no fixed place. System requirements sat in `documentation/`, one working agreement sat at the repository root, and the other sat in its own directory. The README still said the team would decide where documents live.

## Decision

Follow [Where to put documents](../documentation/README.md).

System requirements stay in `documentation/system-requirements.md`. Each subsystem keeps its own documents in `documentation/subsystems/<name>/`. Interface agreements go in `documentation/interfaces/`, one file per interface, named after the two subsystems. Decision records stay in this folder.

## Alternatives we considered

Leaving the location to each author, and pointing people at a Slack message. Slack is where the weekly updates already go, and a new teammate would still not find the document from the repository.

A separate repository for each subsystem. The system is one system, and an interface agreement needs both owners on the same pull request.

## Consequences

The two working agreements now live in their subsystem folders. The old paths point to the new files. System requirements are unchanged and still a draft. A later decision can change the map.

# 0004: Supported repositories are a plain-text list

**Date:** 2026-11-11
**Status:** proposed
**Deciders:** Integration subsystem (Meshaal Aldawood); accepted when the pull request is approved

## Context

INT-1 says Integration receives bug reports from "supported GitHub repositories". Nothing says which ones. Gate 4 requires at least three open source projects that differ in size and application domain, and the team has not chosen them.

## Decision

The supported repositories are an allowlist in `src/integration/supported_repos.txt`, one `owner/repo` per line, case-insensitive. It is seeded with 8 test repositories. Adding one means adding a line and restarting the server. A report from any other repository gets the message "This repository is not supported yet".

## Alternatives we considered

Accepting any public repository. This does not match INT-1, and we cannot show the system works on projects we have not looked at.

A database or settings page. A text file can be read and changed in a pull request, and that is enough for now.

## Consequences

The eight seeds are for testing and demos. They are not the evaluation projects. The final three for Gate 4 are a team decision still to make, and this file will change then. Changing the list needs no code change.

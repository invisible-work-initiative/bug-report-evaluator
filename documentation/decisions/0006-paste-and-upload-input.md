# 0006: Paste and upload as extra input

**Date:** 2026-11-11
**Status:** proposed
**Deciders:** Integration subsystem (Meshaal Aldawood); accepted when the pull request is approved

## Context

INT-1 covers GitHub issues. For demos, a maintainer or reviewer may want to try a report that is not on GitHub, or is not yet filed. IE's draft requires `repository`, `issue_number`, `issue_url`, `created_at` and `updated_at`, and does not say what to do when they are missing. We have asked IE whether a variant without them is acceptable. The question is open.

## Decision

The web interface accepts a GitHub issue URL, pasted text, or an uploaded file. For paste and upload, the fields only GitHub can supply stay empty. They are never invented. These records are labeled as outside the current IE agreement. Acceptance is pending IE's answer.

## Alternatives we considered

GitHub URLs only. It matches INT-1 and the IE draft exactly, but a demo then needs a real issue every time.

Filling the missing fields with placeholders such as a made-up issue number. It would pass IE's checks and would be false information, which INT-2 forbids.

## Consequences

Demos are easier. IE may reject these records or ask us to drop the feature, and we would then remove paste and upload or keep them for the demo only. The empty fields must be handled everywhere the report is shown.

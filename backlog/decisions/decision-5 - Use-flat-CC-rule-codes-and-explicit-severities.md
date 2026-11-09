---
id: decision-5
title: Use flat CC rule codes and explicit severities
date: '2026-11-08'
status: accepted
---

## Context

Rule codes are the public contract: they appear in `--select`, `--ignore`,
`# noqa` comments and CI output. Rude 0.1a4's prefix matcher
(`_prefix_matches`) only treats a prefix as matching when the character
after it is a digit, so hyphenated codes such as `CC-SRP001` are silently
not selected by `select = ["CC"]` (verified against the installed
`rude 0.1a4`). Rude rules also default to `Severity.ERROR`, the only level
that fails CI.

## Decision

Planned codes are flat, family encoded in the first digit: `CC1xx`
functions, `CC2xx` classes, `CC3xx` KISS/complexity, `CC4xx` naming,
`CC5xx` DRY, `CC6xx` SOLID heuristics, `CC7xx` dependencies, so `CC`,
`CC1` and `CC101` all select. Every rule sets its severity explicitly:
deterministic and structural rules `WARNING`, heuristic and semantic
rules `INFO`; no rule ships as `ERROR` without a new decision.

## Consequences

Codes are less self-describing than `CC-SRP001`; the catalogue in the
specification (doc-1) is the naming authority and must stay in sync. A
discovery regression test for `select = ["CC"]` is required with the
first rule task.

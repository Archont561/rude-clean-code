---
id: decision-4
title: Keep the package a version-only scaffold
date: '2026-11-08'
status: superseded
---

## Context

The plugin design (rule catalogue, severity contract, configuration
profiles) is specified in `backlog/docs/doc-1`, but no rule has been
implemented or verified against a released Rude. Shipping unverified rule
code as the scaffold would present planned capability as finished.

## Decision

`packages/rude-clean-code/src/rude_clean_code/` contains only
`__init__.py`, exposing only `VERSION` (decision-2). The package's
`features/` and `tests/` contain only the package-version BDD scenario,
which checks `VERSION` against `pyproject.toml`, installed distribution
metadata, the mocked metadata lookup, and the minimal source layout. The
package declares no dependencies, not even Rude.

## Consequences

Rules land incrementally through backlog tasks, each adding its rule,
package-local unit/property tests and feature scenarios in the same
change. The "no other source files" BDD assertion must be relaxed by the
first rule task. Until then, any statement that `rude-clean-code`
enforces Clean Code rules is false; the README and specification say so.

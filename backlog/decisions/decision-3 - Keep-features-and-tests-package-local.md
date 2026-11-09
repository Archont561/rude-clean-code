---
id: decision-3
title: Keep features and tests package-local
date: '2026-11-08'
status: accepted
---

## Context

Tests and behavior specifications need clear ownership in a repository
that may contain several packages.

## Decision

Keep tests and Gherkin feature files within their owning package
(`packages/rude-clean-code/tests/` and `packages/rude-clean-code/features/`);
do not add root-level tests. Repository scripts live under root `scripts/`,
with any script tests under `scripts/tests/`. Keep `examples/` empty until
the public API is stable.

## Consequences

CI and local tasks must point at package-local test paths. Each future
package repeats the package-local version BDD pattern before growing
behavior tests of its own.

---
id: decision-1
title: Ship one rude-clean-code distribution for the plugin
date: '2026-11-08'
status: accepted
---

## Context

The Clean Code ruleset must be installable into any Python repository
alongside Rude, and discoverable through Rude's `rude.plugins` entry-point
mechanism. Splitting rules across distributions would multiply that
contract without benefit at the current scope.

## Decision

Ship one `rude-clean-code` distribution from `packages/rude-clean-code/`.
When rules land, the distribution will register a single `rude.plugins`
entry point and depend on a pinned Rude (`rude>=0.1a4,<0.2` while Rude is
pre-1.0).

## Consequences

One version, one changelog, one entry point to test. Additional
distributions (for example a project-wide indexer, if Rude's per-file rule
API proves insufficient) require a new decision and their own
version-only scaffold first.
